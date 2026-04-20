"""
颜色空间转换工具
HEX → RGB → HSL / LAB
"""


def hex_to_rgb(hex_color: str) -> tuple:
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return r, g, b


def rgb_to_hsl(r: float, g: float, b: float) -> tuple:
    r, g, b = r / 255.0, g / 255.0, b / 255.0
    cmax = max(r, g, b)
    cmin = min(r, g, b)
    delta = cmax - cmin
    l = (cmax + cmin) / 2.0

    if delta == 0:
        h, s = 0.0, 0.0
    else:
        s = delta / (1 - abs(2 * l - 1))
        if cmax == r:
            h = 60 * (((g - b) / delta) % 6)
        elif cmax == g:
            h = 60 * (((b - r) / delta) + 2)
        else:
            h = 60 * (((r - g) / delta) + 4)

    return round(h % 360, 2), round(s * 100, 2), round(l * 100, 2)


def rgb_to_lab(r: float, g: float, b: float) -> tuple:
    def linearize(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r_lin = linearize(r)
    g_lin = linearize(g)
    b_lin = linearize(b)

    x = r_lin * 0.4124564 + g_lin * 0.3575761 + b_lin * 0.1804375
    y = r_lin * 0.2126729 + g_lin * 0.7151522 + b_lin * 0.0721750
    z = r_lin * 0.0193339 + g_lin * 0.1191920 + b_lin * 0.9503041

    xn, yn, zn = 0.95047, 1.00000, 1.08883

    def f(t):
        return t ** (1/3) if t > 0.008856 else 7.787 * t + 16/116

    fx, fy, fz = f(x / xn), f(y / yn), f(z / zn)
    L = 116 * fy - 16
    a = 500 * (fx - fy)
    b_val = 200 * (fy - fz)

    return round(L, 3), round(a, 3), round(b_val, 3)


def hex_to_hsl(hex_color: str) -> tuple:
    return rgb_to_hsl(*hex_to_rgb(hex_color))


def hex_to_lab(hex_color: str) -> tuple:
    return rgb_to_lab(*hex_to_rgb(hex_color))
