"""
单元测试：用真实潘通色验证分类 + 色阶映射
运行：python test_encoder.py
"""
import sys
sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
sys.path.insert(0, '.')

from encoder import generate_skc

TEST_CASES = [
    ("White",       "#F8F8F8", 0, "浅色调 Tint/Light",     "纯白"),
    ("9180 C",      "#EDE8D0", 0, "浅色调 Tint/Light",     "象牙白"),
    ("7527 C",      "#D4C5B0", 0, "浅色调 Tint/Light",     "暖米白"),
    ("100 C",       "#F4ED7C", 1, "浅色调 Tint/Light",     "浅柠檬黄"),
    ("116 C",       "#FFCD00", 1, "浅色调 Tint/Light",     "明黄"),
    ("130 C",       "#E8A000", 1, "中间色调 Mid/Standard",  "金黄H=41°边界"),
    ("1505 C",      "#FF6B00", 2, "中间色调 Mid/Standard",  "亮橙"),
    ("1655 C",      "#FF5C00", 2, "中间色调 Mid/Standard",  "深橙"),
    ("485 C",       "#DA291C", 3, "中间色调 Mid/Standard",  "大红"),
    ("213 C",       "#E8006D", 3, "中间色调 Mid/Standard",  "玫红L<55%归红"),
    ("495 C",       "#F2ACBB", 4, "中间色调 Mid/Standard",  "浅粉"),
    ("510 C",       "#E8A0B4", 4, "中间色调 Mid/Standard",  "中粉"),
    ("2562 C",      "#C589E8", 5, "中间色调 Mid/Standard",  "浅紫"),
    ("2685 C",      "#330072", 5, "深色调 Deep/Dark",       "深紫"),
    ("277 C",       "#9BC4E2", 6, "中间色调 Mid/Standard",  "天蓝"),
    ("286 C",       "#003DA5", 6, "深色调 Deep/Dark",       "宝蓝"),
    ("354 C",       "#00B140", 7, "中间色调 Mid/Standard",  "草绿"),
    ("364 C",       "#4A7729", 7, "中间色调 Mid/Standard",  "墨绿"),
    ("4625 C",      "#5C2E00", 8, "深色调 Deep/Dark",       "深棕L<30%"),
    ("4695 C",      "#7A4B3A", 8, "深色调 Deep/Dark",       "驼色"),
    ("Cool Gray 5", "#B1B3B3", 9, "中间色调 Mid/Standard",  "中灰"),
    ("Black C",     "#2B2B2C", 9, "深色调 Deep/Dark",       "黑"),
]

FAMILY_NAMES = {
    0:"白/米白", 1:"黄", 2:"橙", 3:"红",
    4:"粉", 5:"紫", 6:"蓝", 7:"绿", 8:"棕", 9:"灰/黑"
}


def run_tests():
    passed = failed = review_flagged = 0
    print("=" * 76)
    print(f"{'潘通色号':<14} {'HEX':<10} {'SKC':<6} {'期望':<4} {'实际':<4} {'色阶区间':<22} 结果")
    print("=" * 76)

    for pantone, hex_val, exp_family, exp_range, note in TEST_CASES:
        r = generate_skc(hex_val)
        af = r["family"]
        ar = r["shade_range"]
        skc = r["skc"] or "----"
        ok = af == exp_family and exp_range in ar

        if ok:
            status = "✅"
            passed += 1
        else:
            status = f"❌ 期望{exp_family}/{exp_range}"
            failed += 1

        if r["needs_review"]:
            status += " ⚠️"
            review_flagged += 1

        print(f"{pantone:<14} {hex_val:<10} {skc:<6} {exp_family}号   {af}号   {ar:<22} {status}")
        if not ok:
            h, s, l = r["hsl"]
            print(f"  └─ HSL=({h}°,{s}%,{l}%) LAB-L={r['lab'][0]}  {note}")

    print("=" * 76)
    total = len(TEST_CASES)
    print(f"结果：{passed}/{total} 通过  {failed} 失败  {review_flagged} 标记审核")
    print(f"准确率：{passed/total*100:.1f}%")
    return failed == 0


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
