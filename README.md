# SKC 颜色编码系统

**SKC Color Encoding System**
潘通（Pantone）全系列色卡 → 6位SKC编码自动生成系统

---

## 快速上手

**双击 `SKC_Query_v3.html`** 在浏览器打开，离线即可使用：

- 支持全部 15 种潘通色卡系列
- 输入任意格式色号（见下方格式说明）
- 输出：6位SKC编码 + 颜色预览 + 色系 + 跨系列关联
- 无需安装任何依赖，单文件离线运行

---

## SKC 编码规则

```
SKC = [色系编号(1位)] + [色阶(5位)]
示例：664514 = 蓝色系(6) + 色阶64514(中深蓝)
```

| 编号 | 色系 | 编号 | 色系 |
|:---:|---|:---:|---|
| 0 | 白/米白 | 5 | 紫/薰衣草 |
| 1 | 黄/米黄 | 6 | 蓝/天蓝 |
| 2 | 橙/珊瑚 | 7 | 绿/薄荷 |
| 3 | 红/玫红 | 8 | 棕/卡其 |
| 4 | 粉/裸色 | 9 | 灰/黑 |

色阶范围：`10000`（最浅/白）→ `99999`（最深/黑），总容量 **10色系 × 90,000 = 900,000 slots**。

---

## 支持的潘通系列

| 系列标识 | 名称 | 色数 |
|---|---|---|
| TPG | 纺织家居纸质色彩 | 2,626 |
| TCX | 纺织家居棉布色彩 | 2,626 |
| TPX | 纺织家居纸质色彩（旧版） | 2,100 |
| TSX | 纺织行业涤纶 | 203 |
| TPM | 纺织金属闪光色 | 200 |
| TN  | 尼龙鲜艳色 | 21 |
| SP  | 皮肤色彩 | 110 |
| C   | 专色印刷光面铜版纸 | 2,390 |
| U   | 专色印刷哑面胶版纸 | 2,389 |
| PC  | CMYK四色印刷光面 | 2,868 |
| PU  | CMYK四色印刷哑面 | 2,868 |
| CP  | 色彩桥梁光面 | 2,135 |
| UP  | 色彩桥梁哑面 | 2,135 |
| METAL | 金属色 | 656 |
| PASTEL | 粉彩/霓虹色 | 392 |
| **合计** | | **23,719** |

---

## 查询格式说明

HTML 查询工具支持以下所有输入格式：

| 输入示例 | 匹配系列 |
|---|---|
| `19-4150TPG` | 纺织 TPG |
| `19-4150 TCX` | 纺织 TCX（空格可选）|
| `19-4150TPX` / `19-4150 TPX` | 纺织 TPX |
| `19-4150` | 自动匹配首选系列（TPG优先）|
| `100 C` | 印刷 C 面 |
| `877 U` | 印刷 U 面 |
| `P 1-1 C` | CMYK 印刷 PC |
| `8965 C` | 金属色 METAL |
| `801 C` | 粉彩/霓虹 PASTEL |
| `17-2435TN` | 尼龙 TN |

---

## 文件说明

| 文件 | 说明 |
|---|---|
| `SKC_Query_v3.html` | **离线查询工具（主入口）**，内嵌 23,719 条全系列数据 |
| `import_all.py` | 全量导入脚本，从 xlsx 重建 `skc_master.db` |
| `build_html.py` | 从数据库生成 `SKC_Query_v3.html` |
| `color_utils.py` | HEX → HSL / LAB 颜色空间转换 |
| `classifier.py` | 色系分类引擎（0–9，12条优先级规则）|
| `shade_mapper.py` | 色阶映射（10000–99999）|
| `encoder.py` | 单色编码入口 |
| `batch_encoder.py` | 批量编码（零碰撞保障）|
| `database.py` | SQLite 去重锁定数据库 |
| `excel_tool.py` | Excel 自动填充工具 |
| `export_review.py` | 导出边界色审核队列 |
| `import_review.py` | 导入审核结论回数据库 |
| `api.py` | REST API 服务（Flask）|
| `test_encoder.py` | 单元测试 |

> `skc_master.db` 不纳入版本控制，可随时由 `import_all.py` 重建。

---

## 环境要求

```bash
pip install flask openpyxl pdfplumber
```

Python 3.10+，SQLite 内置无需额外安装。

---

## 数据库重建

当潘通数据源更新时，运行：

```bash
# 验证（不写入数据库）
python import_all.py --dry-run

# 正式重建（删除旧库，重新导入全部 15 个系列）
python import_all.py
```

数据源路径在 `import_all.py` 顶部 `CATALOG_DIR` 变量中配置。

重建完成后更新 HTML：

```bash
python build_html.py
```

---

## Python API

### 单色编码

```python
from encoder import generate_skc

result = generate_skc('#003DA5')
print(result['skc'])         # '664514'
print(result['family'])      # 6
print(result['shade_range']) # 'Deep/Dark'
```

### 数据库查询

```python
from database import lookup, lookup_all_series

# 查询单条（支持任意系列后缀）
rec = lookup('19-4150TPG')
print(rec['skc'])    # '664514'
print(rec['series']) # 'TPG'

# 查询同 base 所有系列
all_series = lookup_all_series('19-4150TPG')
for r in all_series:
    print(r['series'], r['skc'])
```

### 注册新颜色

```python
from database import register

register({
    'pantone':      '新色号-TPG',
    'name':         'New Color',
    'hex':          '#RRGGBB',
    'rgb':          'R,G,B',
    'series':       'TPG',
    'family':       6,
    'shade':        64000,
    'shade_range':  'Mid/Standard',
    'lab_l':        50.0,
    'lab_a':        0.0,
    'lab_b':        0.0,
    'needs_review': False,
})
```

---

## REST API

```bash
python api.py
# 服务运行在 http://127.0.0.1:5000
```

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/encode` | 潘通号或 HEX → SKC |
| GET  | `/api/lookup/<skc>` | SKC → 完整色彩信息 |
| GET  | `/api/search` | 按名称/色系搜索 |
| GET  | `/api/review` | 获取待审核列表 |
| POST | `/api/review/confirm` | 提交审核结论 |
| GET  | `/api/stats` | 数据库统计 |

```bash
# 查询示例
curl -X POST http://127.0.0.1:5000/api/encode \
  -H "Content-Type: application/json" \
  -d '{"pantone": "19-4150TPG"}'

curl http://127.0.0.1:5000/api/stats
```

---

## Excel 批量工具

```bash
python excel_tool.py 订单.xlsx 潘通色号列名
# 输出：订单_skc.xlsx（追加 SKC编码、色系、颜色预览列）
```

- 绿色字体：正常编码
- 黄底红字：边界色，需人工确认

---

## 边界色审核

```bash
# 导出待审核队列
python export_review.py

# 业务人员在 review_queue.xlsx 的"审核结论"列填入色系编号

# 导入审核结论
python import_review.py review_queue.xlsx 审核人姓名
```

---

## 数据说明

| 指标 | 数值 |
|---|---|
| 潘通系列数 | 15 种 |
| 总色数 | 23,719 |
| 编码碰撞 | 0 |
| 编码空间总容量 | 900,000 slots |
| 当前利用率 | 2.6%（最高色系 5.2%）|
| 需人工审核 | 1,963 条（8.3%）|
