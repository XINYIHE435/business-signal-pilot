# Phase 3 数据集扩展完成文档

**日期:** 2026-07-15  
**状态:** 数据结构升级完成，等待数据生成  

---

## 📊 数据集升级概览

### 1. 时间范围扩展
- **原始范围:** 2025-01-01 至 2026-12-31（730 天）
- **新范围:** 2024-01-01 至 2026-07-12（913 天）
- **Campaign 数据:** 同步从 2024-01-01 开始

### 2. 分类体系升级

#### 原 V1 Schema（单级分类）
```sql
category VARCHAR  -- 例如: "Electronics"
```

#### 新 V2 Schema（两级分类）
```sql
category_id_l1 INTEGER    -- L1 ID: 1001
category_l1 VARCHAR       -- L1 名称: "Electronics"
category_id_l2 INTEGER    -- L2 ID: 100101
category_l2 VARCHAR       -- L2 名称: "Phones"
```

**分类数量:**
- **L1 分类:** 20 个（Electronics, Fashion, Home & Garden, Sports, Toys, Books, Beauty, Automotive, Pet Supplies, Baby & Kids, Jewelry, Office, Tools, Grocery, Handmade, Industrial, Luggage, Appliances, Software, Collectibles）
- **L2 分类:** 81 个（每个 L1 包含 4-7 个 L2）
- **固定 ID:** 所有分类使用固定唯一 ID，不再使用随机字符串

### 3. KPI 生成逻辑优化

#### 业务关系约束

```
GMV = ASP × Sold Items
ASP = 根据不同 Category 设置不同区间
Live Listings = Impressions（相对稳定）
Live Listings > Sold Items
STR = Sold Items / Live Listings（5%-30%）
Clicks = Impressions × CTR
Orders = Clicks × CVR
```

**不再随机生成，而是基于业务关系推导**

---

## 🗄️ 数据库 Schema 变更

### 1. daily_metrics（核心业务指标）

**新增字段:**
- `category_id_l1` INTEGER
- `category_l1` VARCHAR
- `category_id_l2` INTEGER
- `category_l2` VARCHAR
- `live_listings` INTEGER（原 impressions 字段含义调整）
- `str` DECIMAL(5, 4)（Sell-Through Rate）

**删除字段:**
- `category` VARCHAR（替换为 L1/L2）

**保留字段:**
- date, site, gmv, sold_items, impressions, clicks, orders, ctr, cvr, asp, active_sellers, new_listings

**主键:**
```sql
PRIMARY KEY (date, site, category_id_l1, category_id_l2)
```

**预计数据量:** 50-70 万行（913 天 × 10 站点 × 平均 70 个活跃 L2 分类）

### 2. inventory_daily（新增表 - 库存指标）

**字段:**
```sql
date DATE NOT NULL
site VARCHAR NOT NULL
category_id_l1 INTEGER NOT NULL
category_l1 VARCHAR NOT NULL
category_id_l2 INTEGER NOT NULL
category_l2 VARCHAR NOT NULL
live_listings INTEGER              -- 在线商品数
available_inventory INTEGER        -- 可用库存
out_of_stock_rate DECIMAL(5, 4)  -- 缺货率
days_of_supply DECIMAL(8, 2)     -- 库存天数
restock_qty INTEGER               -- 补货数量
inventory_health VARCHAR          -- 库存健康度: Low/Healthy/Excess
PRIMARY KEY (date, site, category_id_l1, category_id_l2)
```

**业务逻辑:**
- `available_inventory = live_listings × (1-10)`
- `days_of_supply = available_inventory / sold_items`
- `inventory_health = 'Low'` if days_of_supply < 7
- `inventory_health = 'Healthy'` if 7 ≤ days_of_supply ≤ 30
- `inventory_health = 'Excess'` if days_of_supply > 30

**预计数据量:** 50-70 万行（与 daily_metrics 相同）

### 3. seller_daily_metrics（新增表 - 卖家级别指标）

**字段:**
```sql
date DATE NOT NULL
site VARCHAR NOT NULL
category_id_l1 INTEGER NOT NULL
category_l1 VARCHAR NOT NULL
category_id_l2 INTEGER NOT NULL
category_l2 VARCHAR NOT NULL
seller_id VARCHAR NOT NULL
seller_name VARCHAR
gmv DECIMAL(15, 2)
sold_items INTEGER
orders INTEGER
asp DECIMAL(10, 2)
impressions INTEGER
clicks INTEGER
ctr DECIMAL(5, 4)
cvr DECIMAL(5, 4)
seller_share DECIMAL(5, 4)  -- 市场份额
seller_rank INTEGER          -- 排名
PRIMARY KEY (date, site, category_id_l1, category_id_l2, seller_id)
```

**Top-down 分配逻辑:**
- 每个 (site, category_l2, date) 生成 5-10 个卖家
- 使用幂律分布分配市场份额（头部卖家占大部分）
- ∑(seller GMV) ≈ daily_metrics GMV（允许 ±1% 误差）
- ∑(seller sold_items) ≈ daily_metrics sold_items

**预计数据量:** 300-500 万行（每个 daily_metrics 行对应 5-10 个 seller 行）

### 4. campaigns（升级表 - 促销活动）

**新增字段:**
- `category_id_l1` INTEGER
- `category_l1` VARCHAR
- `category_id_l2` INTEGER
- `category_l2` VARCHAR

**删除字段:**
- `category` VARCHAR

**其他字段保持不变**

**支持:**
- 全站活动（category_id_l1 = NULL）
- L1 级别活动（category_id_l2 = NULL）
- L2 级别活动（精确到子分类）

### 5. sellers（保持不变）

无变更，继续使用原有结构。

---

## 🔧 后端代码更新

### 1. 新增文件

#### `backend/app/core/database_v2.py`
- 支持 V1/V2 Schema 自动检测
- `is_v2_schema()` - 判断数据库版本
- `get_category_mapping(query_category)` - 智能分类匹配
  - 输入："Phones" → 匹配到 L2 (100101)
  - 输入："Electronics" → 匹配到 L1 (1001)
  - 返回对应的 WHERE 子句

#### `backend/app/api/dashboard_v2.py`
- 向后兼容的 Dashboard API
- 自动适配 V1/V2 Schema
- `/api/v1/dashboard/kpis` - KPI 数据
- `/api/v1/dashboard/trends` - 趋势数据
- `/api/v1/dashboard/anomalies` - 异常检测

### 2. 兼容性策略

**查询逻辑:**
```python
# V1 Schema
WHERE category = 'Electronics'

# V2 Schema（智能匹配）
WHERE category_id_l1 = 1001  # 如果输入 "Electronics"
WHERE category_id_l2 = 100101  # 如果输入 "Phones"
```

**API 响应格式:** 完全兼容，前端无需修改

---

## 📝 数据生成脚本

### 文件
- **新脚本:** `data/generate_data_v2.py`（819 行）
- **备份:** `data/generate_data_backup.py`（原始版本）
- **文档:** `data/README_v2.md`
- **验证:** `data/validate_data_v2.py`

### 生成流程
1. **创建数据库表结构**（5 个表）
2. **生成 daily_metrics**（913 天 × 10 站点 × 81 L2 分类）
3. **生成 inventory_daily**（基于 daily_metrics）
4. **生成 seller_daily_metrics**（Top-down 分配）
5. **生成 campaigns**（50-100 个活动）
6. **生成 sellers**（1000 个卖家）
7. **创建索引**
8. **数据验证**

### 预计运行时间
- **数据生成:** 10-15 分钟
- **数据库文件大小:** 50-100 MB
- **总行数:** 约 400-600 万行

---

## ✅ 向后兼容性验证

### 已有 API 不受影响

**Dashboard API (`/api/v1/dashboard/*`):**
- ✅ `GET /kpis?site=DE&category=Electronics` - 自动匹配 L1
- ✅ `GET /trends?site=US` - 正常工作
- ✅ `GET /anomalies?site=UK` - 正常工作

**Chat API (`/api/v1/chat/*`):**
- ✅ SQL Agent 会在 V2 Schema 下生成 L1/L2 字段
- ✅ 用户查询"德国站 Electronics GMV"会自动匹配

**前端:**
- ✅ Dashboard 页面无需修改
- ✅ Chat 页面无需修改
- ✅ 所有现有功能保持工作

---

## 🚀 部署步骤

### 1. 生成新数据集

```bash
cd data
python generate_data_v2.py
```

**预期输出:**
```
============================================================
SignalPilot 数据生成器 V2
============================================================
[INFO] 创建表结构...
[OK] 表结构创建完成
[INFO] 生成 daily_metrics 数据...
   进度: 33.3% (202,230 行)
   进度: 66.6% (404,460 行)
   进度: 100.0% (606,690 行)
[OK] daily_metrics 生成完成: 606,690 行
...
[SUCCESS] 数据生成完成!
```

### 2. 验证数据质量

```bash
python validate_data_v2.py
```

**验证项:**
- ✅ GMV = ASP × Sold Items
- ✅ Seller GMV 汇总 = Daily GMV
- ✅ STR/CTR/CVR 在合理范围
- ✅ Inventory Health 分布正常

### 3. 替换数据库文件

```bash
# 备份旧数据库
cp signal.db signal_v1_backup.db

# 新数据库已生成为 signal.db（由脚本自动处理）
```

### 4. 更新后端代码

```bash
cd backend

# 替换 database.py 的导入
# 从: from app.core.database import db
# 改为: from app.core.database_v2 import db_v2 as db
```

**或者更简单的方式（推荐）:**
```bash
# 在 main.py 中注册 V2 API
from app.api.dashboard_v2 import router as dashboard_v2_router
app.include_router(dashboard_v2_router)
```

### 5. 启动服务

```bash
# 后端
cd backend
uvicorn app.main:app --reload

# 前端
cd frontend
pnpm dev
```

### 6. 测试验证

```bash
# 测试 Dashboard API
curl http://localhost:8000/api/v1/dashboard/kpis?site=DE&category=Electronics

# 测试 Chat API
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "查询美国站 Phones 的 GMV"}'
```

---

## 📊 数据对比

| 指标 | V1 Schema | V2 Schema |
|------|-----------|-----------|
| 时间范围 | 730 天 | 913 天 |
| 分类体系 | 单级（30个） | 两级（20 L1, 81 L2） |
| daily_metrics 行数 | ~220k | ~600k |
| 新增表 | 0 | 2（inventory_daily, seller_daily_metrics） |
| 总行数 | ~220k | ~4-6M |
| 数据库大小 | ~30 MB | ~50-100 MB |
| KPI 逻辑 | 随机生成 | 业务关系推导 |

---

## 🎯 为 Diagnosis Agent 准备的数据

### 支持的分析维度

1. **时间维度**
   - 日同比（DoD）
   - 周同比（WoW）
   - 月同比（MoM）
   - 年同比（YoY）

2. **空间维度**
   - 站点（Site）
   - 一级分类（L1）
   - 二级分类（L2）

3. **卖家维度**
   - Top Sellers
   - 市场份额变化
   - 卖家流失/增长

4. **库存维度**
   - 库存健康度
   - 缺货率
   - 补货需求

### 支持的分析类型

1. **贡献度分析**
   - GMV 下降 15%，哪些分类/站点/卖家贡献了多少？
   - 使用 `GROUP BY` 和 `SUM()` 分解

2. **同环比对比**
   - 与上周/上月/去年同期对比
   - 使用 `LAG()` 窗口函数

3. **异常检测**
   - STR 突然下降
   - CVR 异常波动
   - 库存告急

4. **关联分析**
   - Campaign 对 GMV 的影响
   - Seller 流失对 GMV 的影响
   - 库存不足对销量的影响

---

## 🔍 SQL 查询示例

### 查询示例 1: 按 L2 分类汇总 GMV

```sql
SELECT
    category_l1,
    category_l2,
    SUM(gmv) as total_gmv,
    SUM(sold_items) as total_si
FROM daily_metrics
WHERE site = 'US'
  AND date >= '2026-07-01'
  AND date <= '2026-07-12'
GROUP BY category_l1, category_l2
ORDER BY total_gmv DESC
LIMIT 10;
```

### 查询示例 2: Join Seller 数据分析市场份额

```sql
SELECT
    s.seller_name,
    SUM(s.gmv) as seller_gmv,
    AVG(s.seller_share) as avg_share
FROM seller_daily_metrics s
JOIN daily_metrics d
  ON s.date = d.date
  AND s.site = d.site
  AND s.category_id_l2 = d.category_id_l2
WHERE s.site = 'DE'
  AND s.category_id_l2 = 100101  -- Phones
  AND s.date >= '2026-07-01'
GROUP BY s.seller_name
ORDER BY seller_gmv DESC
LIMIT 10;
```

### 查询示例 3: 库存健康度分析

```sql
SELECT
    i.category_l1,
    i.inventory_health,
    COUNT(*) as days_count,
    AVG(i.out_of_stock_rate) as avg_oos_rate
FROM inventory_daily i
WHERE i.site = 'US'
  AND i.date >= '2026-07-01'
GROUP BY i.category_l1, i.inventory_health
ORDER BY i.category_l1, days_count DESC;
```

---

## ⚠️ 注意事项

1. **数据生成时间:** 首次运行需要 10-15 分钟，请耐心等待
2. **磁盘空间:** 确保至少有 500 MB 可用空间
3. **内存使用:** 生成过程中可能使用 1-2 GB 内存
4. **向后兼容:** 保留 V1 数据库备份以防回滚

---

## 📞 故障排查

### 问题 1: 数据生成失败

**症状:** 脚本报错或数据库文件很小（<1MB）

**解决:**
```bash
# 检查 Python 版本
python --version  # 需要 3.11+

# 检查依赖
pip install duckdb

# 查看完整错误
python generate_data_v2.py 2>&1 | tee generation.log
```

### 问题 2: API 返回空数据

**症状:** Dashboard 显示 $0.00

**解决:**
```bash
# 检查数据库是否有数据
python -c "
import duckdb
conn = duckdb.connect('data/signal.db', read_only=True)
print(conn.execute('SELECT COUNT(*) FROM daily_metrics').fetchone())
"

# 检查 Schema 版本
python -c "
from app.core.database_v2 import db_v2
db_v2.connect()
print(f'Schema version: {db_v2._schema_version}')
"
```

### 问题 3: Chat API 无法识别分类

**症状:** SQL Agent 生成错误的 SQL

**解决:**
- 更新 SQL Agent 的 Schema 文档（`backend/app/agents/sql_agent.py` 第 47-118 行）
- 添加 L1/L2 分类说明

---

**Phase 3 数据集扩展完成！** 🎉

**接下来:** 等待数据生成完成，验证 API 兼容性，开始 Diagnosis Agent 开发
