"""
潘通全系列数据库一键导入脚本
从 D:/BaiduNetdiskDownload/潘通全系列数据库 读取全部 15 个 xlsx，
编码后写入 skc_master.db（先清空重建）。

用法：
    python import_all.py           # 完整重建
    python import_all.py --dry-run # 只解析不写库，用于验证
"""
import sys, os, time
sys.path.insert(0, 'C:/Users/jiawa/skc_color')

import openpyxl
from pathlib import Path
from collections import defaultdict

from color_utils import hex_to_lab
from classifier import classify_from_hex
from shade_mapper import shade_to_range
from database import DB_PATH, init_db, register, stats

CATALOG_DIR = Path('D:/BaiduNetdiskDownload/潘通全系列数据库')

# (series标识, 相对路径, 列格式)
# 列格式 A：col[1]=pantone, col[3]=RGB, col[4]=HEX, col[7]=Lab字符串（无独立 name 列）
# 列格式 B：col[1]=name, col[2]=pantone, col[4]=RGB, col[5]=HEX, col[9]=L, col[10]=A, col[11]=B
SERIES_FILES = [
    ('C',      '1.潘通C卡调色配方电子版(2390种色号)/潘通(PANTONE)专色配方指南光面铜版纸C色板(2390种色号).xlsx',      'A'),
    ('U',      '2.潘通U卡调色配方电子版(2390种色号)/潘通(PANTONE)专色配方指南哑面胶版纸U色板(2390种色号).xlsx',      'B'),
    ('TCX',    '3.潘通TCX卡调色配方电子版(2626种色号)/潘通(PANTONE)纺织+家居棉布色彩TCX色板(2626种色号).xlsx',      'B'),
    ('TPG',    '4.潘通TPG卡调色配方电子版(2626种色号)/潘通(PANTONE)纺织+家居纸质色彩TPG色板(2626种色号).xlsx',      'B'),
    ('TPX',    '5.潘通TPX卡调色配方电子版(2100种色号)/潘通(PANTONE)纺织+家居纸质色彩TPX色板(2100种色号).xlsx',      'B'),
    ('TSX',    '6.潘通TSX卡调色配方电子版(203种色号)/潘通(PANTONE)纺织行业涤纶TSX色板(203种色号).xlsx',            'B'),
    ('PASTEL', '7.潘通粉彩卡调色配方电子版(420种色号)/潘通(PANTONE)粉彩霓虹色色卡(420种色号).xlsx',               'A'),
    ('METAL',  '8.潘通金属卡调色配方电子版(656种色号)/潘通(PANTONE)金属色配方指南光面铜版纸(656种色号).xlsx',        'B'),
    ('PC',     '9.潘通PC卡调色配方电子版(2868种色号)/潘通(PANTONE)四色叠印指南光面铜版纸C色板(2868种色号).xlsx',     'B'),
    ('PU',     '10.潘通PU卡调色配方电子版(2868种色号)/潘通(PANTONE)四色叠印指南哑面胶版纸U色板(2868种色号).xlsx',    'B'),
    ('CP',     '11.潘通CP卡调色配方电子版(2143种色号)/潘通(PANTONE)色彩桥梁光面铜版纸C色板(2143种色号).xlsx',       'B'),
    ('UP',     '12.潘通UP卡调色配方电子版(2135种色号)/潘通(PANTONE)色彩桥梁哑面胶版纸U色板(2135种色号).xlsx',       'B'),
    ('TPM',    '13.潘通TPM卡调色配方电子版(200种色号)/潘通(PANTONE)闪光金属色指南TPM色板(200种色号).xlsx',          'B'),
    ('TN',     '14.潘通TN卡调色配方电子版(21种色号)/潘通(PANTONE)尼龙鲜艳色TN色板(21种色号).xlsx',                'B'),
    ('SP',     '15.潘通皮肤卡调色配方电子版(110种色号)/潘通(PANTONE)皮肤色彩指南(110种色号).xlsx',                 'B'),
]


def _safe_str(v) -> str:
    return str(v).strip() if v is not None else ''


def _safe_float(v):
    try:
        return float(v)
    except (TypeError, ValueError):
        return None


def _valid_hex(v) -> bool:
    s = _safe_str(v)
    if s.startswith('#') and len(s) == 7:
        try:
            int(s[1:], 16)
            return True
        except ValueError:
            pass
    return False


def _parse_lab_str(s) -> tuple:
    """'91.63,-12.65,66.38' → (91.63, -12.65, 66.38)"""
    try:
        parts = str(s).split(',')
        if len(parts) >= 3:
            return float(parts[0]), float(parts[1]), float(parts[2])
    except (ValueError, AttributeError):
        pass
    return None, None, None


def parse_xlsx(series: str, path: str, fmt: str) -> list[dict]:
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb.active
    rows = []
    for i, row in enumerate(ws.iter_rows(values_only=True)):
        if i < 2:  # 跳过标题行和表头行
            continue
        if fmt == 'A':
            pantone = _safe_str(row[1] if len(row) > 1 else None)
            rgb     = _safe_str(row[3] if len(row) > 3 else None)
            hex_val = _safe_str(row[4] if len(row) > 4 else None)
            lab_l, lab_a, lab_b = _parse_lab_str(row[7] if len(row) > 7 else None)
            name = ''
        else:  # fmt B
            name    = _safe_str(row[1] if len(row) > 1 else None)
            pantone = _safe_str(row[2] if len(row) > 2 else None)
            rgb     = _safe_str(row[4] if len(row) > 4 else None)
            hex_val = _safe_str(row[5] if len(row) > 5 else None)
            lab_l   = _safe_float(row[9]  if len(row) > 9  else None)
            lab_a   = _safe_float(row[10] if len(row) > 10 else None)
            lab_b   = _safe_float(row[11] if len(row) > 11 else None)

        if not pantone or not _valid_hex(hex_val):
            continue

        # 如果 xlsx 里没有 LAB，从 HEX 计算
        if lab_l is None:
            lab_l, lab_a, lab_b = hex_to_lab(hex_val)

        rows.append({
            'pantone': pantone,
            'name':    name,
            'hex':     hex_val.upper(),
            'rgb':     rgb,
            'series':  series,
            'lab_l':   lab_l,
            'lab_a':   lab_a,
            'lab_b':   lab_b,
        })
    wb.close()
    return rows


def map_shade_base(l_star: float) -> int:
    raw = round((1 - l_star / 100) * 89999) + 10000
    return max(10000, min(99999, raw))


def batch_encode(all_rows: list[dict]) -> list[dict]:
    """
    全局批量编码：
    1. 按色系分组，组内按 L* 降序（浅→深）排列
    2. 同色系内按 L* 步进分配色阶，碰撞时 +1
    3. 跨系列同色号（pantone_base 相同）共享同一色阶空间，
       各系列独立 pantone 但色阶相邻——视觉上"同色"的 SKC 数字相近
    """
    # 先算每行的 family
    for r in all_rows:
        clf = classify_from_hex(r['hex'])
        r['family']       = clf['family']
        r['needs_review'] = clf['needs_review']
        if r['lab_l'] is None:
            r['lab_l'], r['lab_a'], r['lab_b'] = clf['lab']

    # 按色系分组，组内按 L* 降序
    by_family = defaultdict(list)
    for r in all_rows:
        by_family[r['family']].append(r)
    for fam in by_family:
        by_family[fam].sort(key=lambda x: (-x['lab_l'], x['lab_a'], x['lab_b']))

    results = []
    for fam in sorted(by_family.keys()):
        used = set()
        for r in by_family[fam]:
            base  = map_shade_base(r['lab_l'])
            shade = base
            while shade in used and shade <= 99999:
                shade += 1
            if shade > 99999:
                shade = base - 1
                while shade in used and shade >= 10000:
                    shade -= 1
            used.add(shade)
            skc = '%d%05d' % (fam, shade) if fam != -1 else None
            results.append({
                **r,
                'skc':         skc,
                'shade':       shade,
                'shade_range': shade_to_range(shade),
            })
    return results


def run(dry_run: bool = False):
    # 1. 读取所有 xlsx
    all_rows = []
    print('=== 读取 xlsx ===')
    for series, rel_path, fmt in SERIES_FILES:
        path = str(CATALOG_DIR / rel_path)
        rows = parse_xlsx(series, path, fmt)
        print(f'  {series:8s}: {len(rows)} 条')
        all_rows.extend(rows)
    print(f'合计: {len(all_rows)} 条\n')

    # 2. 批量编码
    print('=== 批量编码 ===')
    t0 = time.time()
    encoded = batch_encode(all_rows)
    print(f'编码完成，耗时 {time.time()-t0:.1f}s')

    # 碰撞验证
    skc_list = [r['skc'] for r in encoded if r['skc']]
    collisions = len(skc_list) - len(set(skc_list))
    needs_review = sum(1 for r in encoded if r['needs_review'])
    print(f'碰撞数: {collisions}（应为 0）')
    print(f'需人工审核: {needs_review}\n')

    if dry_run:
        print('--dry-run 模式，不写入数据库')
        return

    # 3. 重建数据库
    print('=== 重建数据库 ===')
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print(f'已删除旧库: {DB_PATH}')
    init_db(DB_PATH)

    created = duplicate = error = 0
    for r in encoded:
        if not r['skc']:
            continue
        record = {
            'pantone':     r['pantone'],
            'name':        r.get('name', ''),
            'hex':         r['hex'],
            'rgb':         r.get('rgb', ''),
            'family':      r['family'],
            'shade':       r['shade'],
            'shade_range': r['shade_range'],
            'lab_l':       r['lab_l'],
            'lab_a':       r['lab_a'],
            'lab_b':       r['lab_b'],
            'needs_review':r['needs_review'],
            'series':      r.get('series', ''),
        }
        try:
            result = register(record, DB_PATH)
            if result['status'] == 'created':
                created += 1
            else:
                duplicate += 1
        except Exception as e:
            error += 1
            print(f'  ERROR {r["pantone"]}: {e}')

    print(f'写入完成: created={created}  duplicate={duplicate}  error={error}\n')

    # 4. 统计
    stats(DB_PATH)


if __name__ == '__main__':
    dry_run = '--dry-run' in sys.argv
    run(dry_run=dry_run)
