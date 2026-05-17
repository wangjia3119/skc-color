"""
SKC 主数据库
- 去重：同一潘通号只生成一次编码
- 锁定：编码写入后不可覆盖
- 碰撞：新色与已有编码冲突时自动步进
- SKC 格式：6位，F SSSSS（色系1位 + 色阶5位）
"""
import sqlite3, csv, time
from contextlib import contextmanager

DB_PATH = 'C:/Users/jiawa/skc_color/skc_master.db'

# 支持的潘通系列后缀（用于解析 pantone_base）
SERIES = ('TPG', 'TCX', 'TPX', 'TSX', 'TPM', 'TN', 'SP',
          'PASTEL', 'METAL', 'PC', 'PU', 'CP', 'UP', 'C', 'U')


def _normalize_pantone(pantone: str) -> tuple[str, str]:
    """
    返回 (base, series)
    例如 '19-4150TPG'  -> ('19-4150', 'TPG')
         '19-4150 TCX' -> ('19-4150', 'TCX')
         '100 C'       -> ('100', 'C')
         '19-4150'     -> ('19-4150', '')
    长后缀优先匹配，避免 'PC' 被误拆成 'C'。
    """
    p = pantone.strip().upper()
    # 按长度降序排，避免短后缀先匹配
    for s in sorted(SERIES, key=len, reverse=True):
        if p.endswith(' ' + s):
            return p[:-len(s)-1].strip(), s
        if p.endswith(s):
            return p[:-len(s)].strip(), s
    return p, ''


def _with_series(base: str, series: str) -> str:
    """将 base 补上系列后缀"""
    return base + series if series else base


def init_db(db_path: str = DB_PATH):
    with sqlite3.connect(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS skc_colors (
            skc          TEXT PRIMARY KEY,
            pantone      TEXT UNIQUE NOT NULL,
            pantone_base TEXT,
            series       TEXT DEFAULT '',
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

        CREATE INDEX IF NOT EXISTS idx_pantone      ON skc_colors(pantone);
        CREATE INDEX IF NOT EXISTS idx_pantone_base ON skc_colors(pantone_base);
        CREATE INDEX IF NOT EXISTS idx_family       ON skc_colors(family);
        CREATE INDEX IF NOT EXISTS idx_status       ON skc_colors(status);
        CREATE INDEX IF NOT EXISTS idx_rq_pantone   ON review_queue(pantone);
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
    """从 base_shade 开始步进，找到未被占用的色阶（范围 10000–99999）"""
    shade = base_shade
    while shade <= 99999:
        existing = conn.execute(
            'SELECT 1 FROM skc_colors WHERE skc=?',
            ('%d%05d' % (family, shade),)
        ).fetchone()
        if not existing:
            return shade
        shade += 1
    # 向下找
    shade = base_shade - 1
    while shade >= 10000:
        existing = conn.execute(
            'SELECT 1 FROM skc_colors WHERE skc=?',
            ('%d%05d' % (family, shade),)
        ).fetchone()
        if not existing:
            return shade
        shade -= 1
    raise ValueError('色系 %d 编码空间已耗尽' % family)


def lookup(pantone: str, db_path: str = DB_PATH) -> dict | None:
    """
    查询潘通号是否已有SKC编码。
    支持任意后缀：19-4150TPG / 19-4150TCX / 19-4150 均可命中同一条记录。
    优先精确匹配，其次按 pantone_base 跨系列匹配。
    """
    base, _ = _normalize_pantone(pantone)
    with get_conn(db_path) as conn:
        # 1. 精确匹配
        row = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone=?',
            (pantone.strip().upper(),)
        ).fetchone()
        if row:
            return dict(row)
        # 2. 按 base 跨系列匹配（取第一条）
        row = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone_base=? LIMIT 1',
            (base,)
        ).fetchone()
        return dict(row) if row else None


def lookup_all_series(pantone: str, db_path: str = DB_PATH) -> list[dict]:
    """
    查出同一 base 下所有系列的记录（用于互转展示）。
    """
    base, _ = _normalize_pantone(pantone)
    with get_conn(db_path) as conn:
        rows = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone_base=? ORDER BY series',
            (base,)
        ).fetchall()
        return [dict(r) for r in rows]


def register(record: dict, db_path: str = DB_PATH) -> dict:
    """
    注册新颜色，返回最终写入的记录。
    record 需包含: pantone, name, hex, rgb, family, shade, shade_range,
                   lab_l, lab_a, lab_b, needs_review
    可选: series（显式指定系列标识，如 'METAL'/'PASTEL'；不传则从 pantone 后缀解析）
    """
    pantone = record['pantone'].strip().upper()
    base, parsed_series = _normalize_pantone(pantone)
    # 优先使用调用方显式传入的 series，否则从 pantone 后缀解析
    series = record.get('series') or parsed_series
    family     = int(record['family'])
    base_shade = int(record['shade'])

    with get_conn(db_path) as conn:
        # 1. 去重检查（精确 pantone）
        existing = conn.execute(
            'SELECT * FROM skc_colors WHERE pantone=?', (pantone,)
        ).fetchone()
        if existing:
            return {'status': 'duplicate', 'record': dict(existing)}

        # 2. 碰撞检查 + 步进
        free_shade = _find_free_skc(conn, family, base_shade)
        skc = '%d%05d' % (family, free_shade)

        # 3. 写入
        now = time.strftime('%Y-%m-%d %H:%M:%S')
        conn.execute("""
            INSERT INTO skc_colors
            (skc, pantone, pantone_base, series, name, hex, rgb, family, shade, shade_range,
             lab_l, lab_a, lab_b, needs_review, status, created_at)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            skc, pantone, base, series,
            record.get('name', ''),
            record.get('hex', ''), record.get('rgb', ''),
            family, free_shade, record.get('shade_range', ''),
            record.get('lab_l', 0), record.get('lab_a', 0), record.get('lab_b', 0),
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
            """, (pantone, record.get('name', ''), record.get('hex', ''), skc, now))

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

        print('\n各系列分布:')
        for row in conn.execute('SELECT series, COUNT(*) as cnt FROM skc_colors GROUP BY series ORDER BY series'):
            print('  %-8s: %d' % (row[0] or '(无)', row[1]))

        print('\n各色系分布:')
        names = {0:'白/米白',1:'黄',2:'橙',3:'红',4:'粉',5:'紫',6:'蓝',7:'绿',8:'棕',9:'灰/黑'}
        for row in conn.execute('SELECT family, COUNT(*) as cnt FROM skc_colors GROUP BY family ORDER BY family'):
            slots = 90000
            print('  %d %-6s: %d / %d (%.1f%%)' % (
                row[0], names.get(row[0],'?'), row[1], slots, row[1]/slots*100))


if __name__ == '__main__':
    import os
    db_path = DB_PATH
    if os.path.exists(db_path):
        os.remove(db_path)
    init_db(db_path)
    import_from_csv('C:/Users/jiawa/skc_color/pantone_skc_v2.csv', db_path)
    stats(db_path)