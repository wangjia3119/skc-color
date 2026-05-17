"""
批量编码器：为整个潘通库生成无碰撞SKC编码
策略：
  1. L* 映射初始色阶（step=1）
  2. 同色系内按 (L*, a*, b*) 排序
  3. 碰撞时步进 +1 直到找到空位
"""
import sys
sys.path.insert(0, 'C:/Users/jiawa/skc_color')

import csv
from collections import defaultdict
from color_utils import hex_to_lab
from classifier import classify_from_hex
from shade_mapper import shade_to_range


def map_shade_base(l_star: float) -> int:
    raw = round((1 - l_star / 100) * 89999) + 10000
    return max(10000, min(99999, raw))


def encode_batch(input_rows: list) -> list:
    """
    input_rows: [{'pantone', 'name', 'hex', 'rgb'}, ...]
    返回每行追加 skc, family, shade, shade_range, needs_review
    """
    # 1. 计算每行的 LAB + 色系
    enriched = []
    for r in input_rows:
        clf = classify_from_hex(r['hex'])
        lab = clf['lab']
        enriched.append({
            **r,
            'family':       clf['family'],
            'needs_review': clf['needs_review'],
            'lab_l':        lab[0],
            'lab_a':        lab[1],
            'lab_b':        lab[2],
        })

    # 2. 按色系分组，组内按 (L*, a*, b*) 排序（浅→深，同明度按色调排）
    by_family = defaultdict(list)
    for r in enriched:
        by_family[r['family']].append(r)

    for fam in by_family:
        by_family[fam].sort(key=lambda x: (x['lab_l'], x['lab_a'], x['lab_b']), reverse=True)

    # 3. 逐色系分配编码，碰撞时步进 +1
    results = []
    for fam in sorted(by_family.keys()):
        used = set()
        for r in by_family[fam]:
            base = map_shade_base(r['lab_l'])
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


if __name__ == '__main__':
    import pdfplumber, re

    pdf_path = 'D:/BaiduNetdiskDownload/4.潘通TPG卡调色配方电子版(2626种色号)/潘通(PANTONE)纺织+家居纸质色彩TPG色板(2626种色号).pdf'
    raw_rows = []
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue
            for line in text.split('\n'):
                # 兼容 TPG 和 TCX 后缀
                m = re.match(r'^\d+\s+(.+?)\s+(\d{2}-\d{4}(?:TPG|TCX))\s+(\d+,\d+,\d+)\s+(#[0-9A-Fa-f]{6})', line)
                if m:
                    raw_rows.append({'pantone': m.group(2), 'name': m.group(1).strip(),
                                     'rgb': m.group(3), 'hex': m.group(4)})

    print('extracted: %d colors' % len(raw_rows))
    results = encode_batch(raw_rows)

    # 验证无碰撞
    skc_set = [r['skc'] for r in results if r['skc']]
    collisions = len(skc_set) - len(set(skc_set))
    print('collisions after batch encode:', collisions)

    # 写CSV
    out = 'C:/Users/jiawa/skc_color/pantone_skc_v2.csv'
    fields = ['pantone','name','hex','rgb','skc','family','shade','shade_range','needs_review','lab_l','lab_a','lab_b']
    with open(out, 'w', newline='', encoding='utf-8-sig') as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction='ignore')
        w.writeheader()
        w.writerows(results)
    print('saved:', out)

    # 色系分布
    from collections import Counter
    names = {'0':'白/米白','1':'黄','2':'橙','3':'红','4':'粉','5':'紫','6':'蓝','7':'绿','8':'棕','9':'灰/黑','-1':'未分类'}
    dist = Counter(str(r['family']) for r in results)
    for k in sorted(dist, key=lambda x: int(x)):
        print('  %s %s: %d' % (k, names.get(k,'?'), dist[k]))
    review = sum(1 for r in results if r['needs_review'])
    print('needs_review:', review)
