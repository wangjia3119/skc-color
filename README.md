# SKC 颜色编码自动生成系统

**SKC Color Encoding System**
潘通（Pantone）TPG 色卡 → 4位SKC编码自动生成智能体

---

## 快速上手（推荐）

**双击 `SKC_Query.html`** 在浏览器打开，输入潘通色号即可查询：

- 输入格式：`19-4150TPG`（回车或点查询）
- 输出：4位SKC编码 + 颜色预览 + 色系 + HEX值
- 无需安装任何依赖，离线可用
- 内置2626色潘通TPG色卡数据

---

## 框架与技术栈

| 层级 | 技术 |
|---|---|
| 语言 | Python 3.10+ |
| 颜色算法 | LAB / HSL 色彩空间（自实现，无外部依赖） |
| 数据库 | SQLite（内置，零配置） |
| API 服务 | Flask 3.x |
| Excel 处理 | openpyxl |
| PDF 提取 | pdfplumber |
| 打包格式 | ZIP（0.35 MB） |

---

## 核心技术特性

**编码规则**
```
SKC = [色系0–9] + [色阶100–999]
示例：6280 = 蓝色系 + 中深色阶
```

**分类引擎**
- 输入 HEX → 转 HSL + LAB 双空间
- 12条优先级规则顺序判断（无彩色→米白→棕→黄→橙→红→粉→紫→蓝→绿）
- 棕色二次过滤（暗橙色与橙色共享色相角，用 L* + S 区分）
- 4个灰色地带自动标记人工审核

**色阶映射公式**
```
shade = round((1 - L*/100) × 899) + 100
```
L* 越高（越浅）→ 色阶越小，L* 越低（越深）→ 色阶越大

**零碰撞保障**
- 同色系内按 (L*, a*, b*) 三维排序
- 碰撞时自动步进 +1 找最近空位
- 去重锁定：同一潘通号永远返回同一SKC

---

## 数据规模

| 指标 | 数值 |
|---|---|
| 潘通色总数 | 2626色 |
| 编码碰撞 | 0 |
| 自动分类准确率 | 100%（22色验证） |
| 边界色人工审核 | 234条（8.9%） |
| 数据库大小 | 0.35 MB |

---

## 编码规则

```
SKC = [色系编号(1位)] + [色阶(3位)]

示例：6280 = 蓝色系(6) + 色阶280(中深蓝)
```

| 编号 | 色系 | 编号 | 色系 |
|:---:|---|:---:|---|
| 0 | 白/米白 | 5 | 紫/薰衣草 |
| 1 | 黄/米黄 | 6 | 蓝/天蓝 |
| 2 | 橙/珊瑚 | 7 | 绿/薄荷 |
| 3 | 红/玫红 | 8 | 棕/卡其 |
| 4 | 粉/裸色 | 9 | 灰/黑 |

色阶范围：`100`（最浅）→ `999`（最深），`000–099` 保留给金属/荧光特殊色。

---

## 环境要求

```bash
pip install flask openpyxl pdfplumber
```

---

## 文件说明

| 文件 | 说明 |
|---|---|
| `color_utils.py` | HEX → HSL / LAB 颜色空间转换 |
| `classifier.py` | 色系分类引擎（0–9） |
| `shade_mapper.py` | 色阶映射（100–999） |
| `encoder.py` | 单色编码入口 |
| `batch_encoder.py` | 批量编码（零碰撞保障） |
| `database.py` | SQLite 去重锁定数据库 |
| `excel_tool.py` | Excel 自动填充工具 |
| `export_review.py` | 导出边界色审核队列 |
| `import_review.py` | 导入审核结论回数据库 |
| `api.py` | REST API 服务 |
| `test_encoder.py` | 单元测试（22个潘通色） |
| `skc_master.db` | SQLite 主数据库（2628色） |
| `pantone_skc_v2.csv` | 完整编码对照表 |
| `review_queue.xlsx` | 边界色审核队列 |

---

## 快速使用

### 1. 单色查询（Python）

```python
from encoder import generate_skc

result = generate_skc('#003DA5')
print(result['skc'])        # '6730'
print(result['family'])     # 6
print(result['shade_range'])# 'Deep/Dark'
```

### 2. Excel 批量填充（跟单员）

准备一个 Excel 文件，确保有一列包含潘通色号（如 `11-4001TPG`）：

```bash
python excel_tool.py 订单.xlsx 潘通色号
# 输出：订单_skc.xlsx（原文件追加SKC编码、色系、颜色预览列）
```

- 绿色字体：正常编码
- 黄底红字：边界色，需人工确认

### 3. 启动 REST API

```bash
python api.py
# 服务运行在 http://127.0.0.1:5000
```

#### 接口列表

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/api/encode` | 潘通号或HEX → SKC |
| GET | `/api/lookup/<skc>` | SKC → 完整色彩信息 |
| GET | `/api/search` | 按名称/色系搜索 |
| GET | `/api/review` | 获取待审核列表 |
| POST | `/api/review/confirm` | 提交审核结论 |
| GET | `/api/stats` | 数据库统计 |

#### 接口示例

```bash
# 查询潘通色号
curl -X POST http://127.0.0.1:5000/api/encode \
  -H "Content-Type: application/json" \
  -d '{"pantone": "19-4150TPG"}'

# 实时计算HEX
curl -X POST http://127.0.0.1:5000/api/encode \
  -H "Content-Type: application/json" \
  -d '{"hex": "#003DA5"}'

# 按SKC反查
curl http://127.0.0.1:5000/api/lookup/6648

# 搜索颜色
curl "http://127.0.0.1:5000/api/search?name=coral&limit=5"
curl "http://127.0.0.1:5000/api/search?family=6&limit=10"

# 统计
curl http://127.0.0.1:5000/api/stats
```

### 4. 边界色审核流程

```bash
# Step 1：导出审核队列
python export_review.py
# 生成 review_queue.xlsx

# Step 2：业务人员打开 review_queue.xlsx
# 在"审核结论"列填入色系编号（如 1、2、1 黄 均可）

# Step 3：导入审核结论
python import_review.py review_queue.xlsx 审核人姓名
```

### 5. 新增潘通色入库

```python
from database import register

register({
    'pantone':     '新色号-TPG',
    'name':        '颜色英文名',
    'hex':         '#RRGGBB',
    'rgb':         'R,G,B',
    'family':      6,        # 色系编号
    'shade':       500,      # 初始色阶（系统自动避让碰撞）
    'shade_range': 'Mid/Standard',
    'lab_l':       50.0,
    'lab_a':       0.0,
    'lab_b':       0.0,
    'needs_review': False,
})
```

### 6. 运行单元测试

```bash
python test_encoder.py
# 期望：22/22 通过，准确率 100%
```

---

## 生产部署

```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 api:app
```

---

## 数据说明

- 数据来源：潘通 FHI Paper TPG 色卡（2626色）
- 分类准确率：100%（22个典型色验证）
- 边界色（需人工确认）：234条（8.9%）
- 编码碰撞：0
