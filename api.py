"""
SKC 颜色编码 REST API
端口: 5000

接口列表:
  POST /api/encode          潘通号 → SKC编码
  GET  /api/lookup/<skc>    SKC → 完整色彩信息
  GET  /api/search          搜索颜色（按名称/色系）
  GET  /api/review          获取待审核列表
  POST /api/review/confirm  确认审核结论
  GET  /api/stats           数据库统计
"""
import sys
sys.path.insert(0, 'C:/Users/jiawa/skc_color')

from flask import Flask, request, jsonify
import sqlite3, time
from database import DB_PATH, lookup, register
from encoder import generate_skc

app = Flask(__name__)

FAMILY_NAMES = {
    0:'白/米白', 1:'黄', 2:'橙', 3:'红',
    4:'粉',     5:'紫', 6:'蓝', 7:'绿', 8:'棕', 9:'灰/黑'
}


def _row_to_dict(row):
    if row is None:
        return None
    d = dict(row)
    d['family_name'] = FAMILY_NAMES.get(d.get('family'), '未知')
    d['needs_review'] = bool(d.get('needs_review'))
    return d


@app.post('/api/encode')
def encode():
    body = request.get_json(silent=True) or {}
    pantone = body.get('pantone', '').strip()
    hex_val = body.get('hex', '').strip()

    if not pantone and not hex_val:
        return jsonify({'error': '需要提供 pantone 或 hex 参数'}), 400

    if pantone:
        existing = lookup(pantone.upper())
        if existing:
            return jsonify({
                'source':      'database',
                'skc':         existing['skc'],
                'pantone':     existing['pantone'],
                'name':        existing['name'],
                'hex':         existing['hex'],
                'family':      existing['family'],
                'family_name': FAMILY_NAMES.get(existing['family'], '?'),
                'shade':       existing['shade'],
                'shade_range': existing['shade_range'],
                'needs_review':bool(existing['needs_review']),
                'status':      existing['status'],
            })

    target_hex = hex_val
    if not target_hex:
        return jsonify({'error': '潘通号 %s 不在数据库中，请提供 hex 值' % pantone}), 404

    result = generate_skc(target_hex)
    if result['family'] == -1:
        return jsonify({'error': '无法自动分类，请人工审核', 'hex': target_hex}), 422

    return jsonify({
        'source':      'realtime',
        'skc':         result['skc'],
        'hex':         target_hex,
        'family':      result['family'],
        'family_name': FAMILY_NAMES.get(result['family'], '?'),
        'shade':       result['shade'],
        'shade_range': result['shade_range'],
        'needs_review':result['needs_review'],
        'hsl':         result['hsl'],
        'lab':         result['lab'],
    })


@app.get('/api/lookup/<skc>')
def lookup_skc(skc):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute('SELECT * FROM skc_colors WHERE skc=?', (skc,)).fetchone()
    conn.close()
    if not row:
        return jsonify({'error': 'SKC %s 不存在' % skc}), 404
    return jsonify(_row_to_dict(row))


@app.get('/api/search')
def search():
    name   = request.args.get('name', '')
    family = request.args.get('family', '')
    status = request.args.get('status', '')
    limit  = min(int(request.args.get('limit', 20)), 100)

    sql    = 'SELECT * FROM skc_colors WHERE 1=1'
    params = []
    if name:
        sql += ' AND (name LIKE ? OR pantone LIKE ?)'
        params += ['%'+name+'%', '%'+name+'%']
    if family:
        sql += ' AND family=?'
        params.append(int(family))
    if status:
        sql += ' AND status=?'
        params.append(status)
    sql += ' ORDER BY family, shade LIMIT ?'
    params.append(limit)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify({'count': len(rows), 'results': [_row_to_dict(r) for r in rows]})


@app.get('/api/review')
def get_review():
    family = request.args.get('family', '')
    limit  = min(int(request.args.get('limit', 50)), 200)

    sql = """
        SELECT q.*, s.family, s.shade, s.shade_range, s.lab_l, s.lab_a, s.lab_b
        FROM review_queue q
        LEFT JOIN skc_colors s ON q.pantone=s.pantone
        WHERE q.status='pending'
    """
    params = []
    if family:
        sql += ' AND s.family=?'
        params.append(int(family))
    sql += ' ORDER BY s.family, s.lab_l DESC LIMIT ?'
    params.append(limit)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(sql, params).fetchall()
    conn.close()
    return jsonify({'count': len(rows), 'results': [dict(r) for r in rows]})


@app.post('/api/review/confirm')
def confirm_review():
    body      = request.get_json(silent=True) or {}
    pantone   = body.get('pantone', '').strip().upper()
    final_fam = body.get('final_family')
    reviewer  = body.get('reviewer', 'unknown')

    if not pantone or final_fam is None:
        return jsonify({'error': '需要 pantone 和 final_family'}), 400

    now = time.strftime('%Y-%m-%d %H:%M:%S')
    conn = sqlite3.connect(DB_PATH)

    # 更新审核队列
    conn.execute(
        "UPDATE review_queue SET status='confirmed', reviewer=?, reviewed_at=? WHERE pantone=?",
        (reviewer, now, pantone)
    )
    # 更新主表色系和状态
    conn.execute(
        "UPDATE skc_colors SET family=?, status='active' WHERE pantone=?",
        (int(final_fam), pantone)
    )
    conn.commit()

    row = conn.execute('SELECT * FROM skc_colors WHERE pantone=?', (pantone,)).fetchone()
    conn.row_factory = sqlite3.Row
    conn.close()

    return jsonify({'status': 'confirmed', 'pantone': pantone,
                    'final_family': final_fam, 'family_name': FAMILY_NAMES.get(int(final_fam), '?')})


@app.get('/api/stats')
def stats():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    total   = conn.execute('SELECT COUNT(*) as n FROM skc_colors').fetchone()['n']
    active  = conn.execute("SELECT COUNT(*) as n FROM skc_colors WHERE status='active'").fetchone()['n']
    pending = conn.execute("SELECT COUNT(*) as n FROM skc_colors WHERE status='pending_review'").fetchone()['n']
    review  = conn.execute("SELECT COUNT(*) as n FROM review_queue WHERE status='pending'").fetchone()['n']

    dist_rows = conn.execute(
        'SELECT family, COUNT(*) as cnt FROM skc_colors GROUP BY family ORDER BY family'
    ).fetchall()
    conn.close()

    dist = [{'family': r['family'], 'name': FAMILY_NAMES.get(r['family'],'?'),
              'count': r['cnt']} for r in dist_rows]

    return jsonify({
        'total': total, 'active': active,
        'pending_review': pending, 'review_queue': review,
        'family_distribution': dist
    })


if __name__ == '__main__':
    print('SKC API starting on http://127.0.0.1:5000')
    print('Endpoints:')
    print('  POST /api/encode')
    print('  GET  /api/lookup/<skc>')
    print('  GET  /api/search?name=&family=&limit=')
    print('  GET  /api/review?family=&limit=')
    print('  POST /api/review/confirm')
    print('  GET  /api/stats')
    app.run(debug=False, port=5000)
