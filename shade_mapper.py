"""
色阶映射引擎（后5位数字，范围 10000–99999）
SKC 格式：F SSSSS（6位），F=色系(0-9)，SSSSS=色阶(10000-99999)
L*=100(白) → shade=10000，L*=0(黑) → shade=99999
容量：10 色系 × 90000 = 900000 slots
"""


def map_shade(l_star: float, step: int = 10) -> int:
    raw = round((1 - l_star / 100) * 89999) + 10000
    raw = max(10000, min(99999, raw))
    if step > 1:
        raw = round(raw / step) * step
        raw = max(10000, min(99990, raw))
    return raw


def shade_to_range(shade: int) -> str:
    if shade < 10000:
        return "特殊保留区（金属/荧光）"
    elif shade <= 29999:
        return "浅色调 Tint/Light"
    elif shade <= 59999:
        return "中间色调 Mid/Standard"
    elif shade <= 89999:
        return "深色调 Deep/Dark"
    else:
        return "极深/特殊效果色"


def build_skc(family: int, shade: int) -> str:
    return f"{family}{shade:05d}"
