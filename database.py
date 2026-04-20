"""
SKC 主数据库
- 去重：同一潘通号只生成一次编码
- 锁定：编码写入后不可覆盖
- 碰撞：新色与已有编码冲突时自动步进
"""
import sqlite3, csv, time
from contextlib import contextmanager

DB_PATH = 'C:/Users/jiawa/skc_color/skc_master.db'


def init_db(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS skc_colors (
            skc          TEXT PRIMARY KEY,
            pantone      TEXT UNIQUE NOT NULL,
            name         TEXT,
            hex          TEXT,
            rgb          TEXT,
            family       INTEGER,
            shade        INTEGER,
            shade_range  TEXT,
            lab_l        REAL,
            lab_a        REAL,
            lab_b        REAL,
            needs_review INTEGER DEFAULT 0,
            status       TEXT DEFAULT 'active',
            created_at   TEXT
        );

        CREATE TABLE IF NOT EXISTS review_queue (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            pantone      TEXT UNIQUE NOT NULL,
            name         TEXT,
            hex          TEXT,
            candidate_1  TEXT,
            candidate_2  TEXT,
            delta_e      REAL,
            status       TEXT DEFAULT 'pending',
            reviewer     TEXT,
            final_skc    TEXT,
            created_at   TEXT,
            reviewed_at  TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_pantone ON skc_colors(pantone);
        CREATE INDEX IF NOT EXISTS idx_family  ON skc_colors(family);
        CREATE INDEX IF NOT EXISTS idx_status  ON skc_colors(status);
        """)
    print('DB initialized:', db_path)


@contextmanager
def get_conn(db_path: str = DB_PATH):
    conn = sqlite3.connect(db_path, timeout=10)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _find_free_skc(conn, family: int, base_shade: int) -> int:
    """从 base_shade 开始步进，找到未被占用的色阶"""
    shade = base_shade
    while shade <= 999:
        existing = conn.execute(
            'SELECT 1 FROM skc_colors WHERE skc=?',
            ('%d%03d' % (family, shade),)
        ).fetchone()
        if not existing:
            return shade
        shade += 1
    # 向下找
    shade = base_shade - 1
    while shade >= 100:
        existing = conn.execute(
            'SELECT 1 FROM skc_colors WHERE skc=?',
            ('%d%03d' % (family, shade),)
        ).fetchone()
        if not existing:
            return shade
        shade -= 1
    raise ValueError('色系 %d 编码空间已耗尽' % family)


def lookup(pantone: str, db_path: str = DB_PATH) -> dict | None:
    """查询潘通号是否已有SKC编码"""
    with get_conn(db_path) as conn:
        row = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone=?',
            (pantone.strip().upper(),)
        ).fetchone()
        return dict(row) if row else None


def register(record: dict, db_path: str = DB_PATH) -> dict:
    """
    注册新颜色，返回最终写入的记录
    record 需包含: pantone, name, hex, rgb, family, shade, shade_range,
                   lab_l, lab_a, lab_b, needs_review
    """
    pantone = record['pantone'].strip().upper()
    family  = int(record['family'])
    base_shade = int(record['shade'])

    with get_conn(db_path) as conn:
        # 1. 去重检查
        existing = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone=?', (pantone,)
        ).fetchone()
        if existing:
            return {'status': 'duplicate', 'record': dict(existing)}

        # 2. 碰撞检查 + 步进
        free_shade = _find_free_skc(conn, family, base_shade)
        skc = '%d%03d' % (family, free_shade)

        # 3. 写入
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO skc_colors
            (skc, pantone, name, hex, rgb, family, shade, shade_range,
             lab_l, lab_a, lab_b, needs_review, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            skc, pantone, record.get('name',''),
            record.get('hex',''), record.get('rgb',''),
            family, free_shade, record.get('shade_range',''),
            record.get('lab_l',0), record.get('lab_a',0), record.get('lab_b',0),
            1 if record.get('needs_review') else 0,
            'pending_review' if record.get('needs_review') else 'active',
            now
        ))

        # 4. 需审核的加入审核队列
        if record.get('needs_review'):
            conn.execute("""
                INSERT OR IGNORE INTO review_queue
                (pantone, name, hex, candidate_1, created_at)
                VALUES (?,?,?,?,?)
            """, (pantone, record.get('name',''), record.get('hex',''), skc, now))

        return {'status': 'created', 'skc': skc, 'shade': free_shade}


def import_from_csv(csv_path: str, db_path: str = DB_PATH):
    """从 pantone_skc_v2.csv 批量导入到数据库"""
    created = duplicate = 0
    with open(csv_path, encoding='utf-8-sig') as f:
        rows = list(csv.DictReader(f))

    for r in rows:
        r['needs_review'] = r.get('needs_review','False') == 'True'
        result = register(r, db_path)
        if result['status'] == 'created':
            created += 1
        else:
            duplicate += 1

    print('导入完成: created=%d  duplicate=%d' % (created, duplicate))


def stats(db_path: str = DB_PATH):
    with get_conn(db_path) as conn:
        total   = conn.execute('SELECT COUNT(*) FROM skc_colors').fetchone()[0]
        active  = conn.execute("SELECT COUNT(*) FROM skc_colors WHERE status='active'").fetchone()[0]
        pending = conn.execute("SELECT COUNT(*) FROM skc_colors WHERE status='pending_review'").fetchone()[0]
        review  = conn.execute("SELECT COUNT(*) FROM review_queue WHERE status='pending'").fetchone()[0]
        print('总记录: %d  active: %d  待审核: %d  审核队列: %d' % (total, active, pending, review))

        print('\n各色系分布:')
        names = {0:'白/米白',1:'黄',2:'橙',3:'红',4:'粉',5:'紫',6:'蓝',7:'绿',8:'棕',9:'灰/黑'}
        for row in conn.execute('SELECT family, COUNT(*) as cnt FROM skc_colors GROUP BY family ORDER BY family'):
            print('  %d %s: %d' % (row[0], names.get(row[0],'?'), row[1]))


if __name__ == '__main__':
    import os
    db_path = DB_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    import_from_csv('C:/Users/jiawa/skc_color/pantone_skc_v2.csv', db_path)
    stats(db_path)
