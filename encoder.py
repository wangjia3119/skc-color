"""
SKC 编码生成器主入口
"""
from classifier import classify_from_hex
from shade_mapper import map_shade, shade_to_range, build_skc


def generate_skc(hex_color: str, step: int = 10) -> dict:
    result = classify_from_hex(hex_color)
    family = result["family"]

    if family == -1:
        return {**result, "skc": None, "shade": None,
                "shade_range": "无法自动分类", "needs_review": True}

    l_star = result["lab"][0]
    shade = map_shade(l_star, step)
    skc = build_skc(family, shade)

    return {
        "skc":          skc,
        "family":       family,
        "shade":        shade,
        "shade_range":  shade_to_range(shade),
        "needs_review": result["needs_review"],
        "hsl":          result["hsl"],
        "lab":          result["lab"],
        "hex":          hex_color,
    }
