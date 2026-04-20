"""
色阶映射引擎（后3位数字）
"""


def map_shade(l_star: float, step: int = 10) -> int:
    raw = round((1 - l_star / 100) * 899) + 100
    raw = max(100, min(999, raw))
    if step > 1:
        raw = round(raw / step) * step
        raw = max(100, min(990, raw))
    return raw


def shade_to_range(shade: int) -> str:
    if shade < 100:
        return "特殊保留区（金属/荧光）"
    elif shade <= 299:
        return "浅色调 Tint/Light"
    elif shade <= 599:
        return "中间色调 Mid/Standard"
    elif shade <= 899:
        return "深色调 Deep/Dark"
    else:
        return "极深/特殊效果色"


def build_skc(family: int, shade: int) -> str:
    return f"{family}{shade:03d}"
