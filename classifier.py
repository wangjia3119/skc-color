"""
色系分类引擎（第1位数字）
"""
from color_utils import hex_to_hsl, hex_to_lab

AMBIGUOUS_ZONES = [
    {"h_min": 40,  "h_max": 46,  "desc": "黄橙边界"},
    {"h_min": 308, "h_max": 315, "desc": "紫粉边界"},
    {"h_min": 185, "h_max": 195, "desc": "蓝绿边界"},
]


def _in_ambiguous_zone(h, s, l):
    for zone in AMBIGUOUS_ZONES:
        if zone["h_min"] <= h <= zone["h_max"]:
            return zone["desc"]
    if 10 <= h <= 50 and 28 <= l <= 32:
        return "棕橙明度边界"
    return None


def classify_family(h, s, l):
    needs_review = _in_ambiguous_zone(h, s, l) is not None

    # ① 无彩色：白
    if s < 8 and l > 85:
        return 0, False

    # ② 无彩色：灰/黑
    if s < 8:
        return 9, False

    # ③ 暖米白A：极高明度暖色相（修复9180C，放宽S至50%）
    if s < 50 and l > 85 and 20 <= h <= 70:
        return 0, False

    # ③B 暖米白B：中高明度低饱和暖色相（修复7527C驼米色）
    if s < 35 and l > 65 and 20 <= h <= 70:
        return 0, False

    # ④ 棕色：极深暖色
    if 10 <= h <= 50 and l < 30:
        return 8, needs_review

    # ⑤ 棕色：中深低饱和暖色
    if 10 <= h <= 50 and s < 45 and l < 60:
        return 8, needs_review

    # ⑥ 黄色（下限从43°降至40°，修复130C金黄）
    if 40 <= h <= 70:
        return 1, needs_review

    # ⑦ 橙色（已排除棕色）
    if 20 <= h < 40:
        return 2, needs_review

    # ⑧ 红色（暖红）
    if h >= 355 or h < 20:
        return 3, False

    # ⑨ 粉色 / 玫红
    if 310 <= h < 355:
        return (4, needs_review) if l > 55 else (3, needs_review)

    # ⑩ 紫色
    if 260 <= h < 310:
        return 5, needs_review

    # ⑪ 蓝色
    if 190 <= h < 260:
        return 6, needs_review

    # ⑫ 绿色
    if 70 <= h < 190:
        return 7, needs_review

    return -1, True


def classify_from_hex(hex_color):
    hsl = hex_to_hsl(hex_color)
    lab = hex_to_lab(hex_color)
    h, s, l = hsl
    family, needs_review = classify_family(h, s, l)
    return {"hex": hex_color, "hsl": hsl, "lab": lab,
            "family": family, "needs_review": needs_review}
