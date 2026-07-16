# generate_data_v2.py 使用说明

## 概述

`generate_data_v2.py` 是 SignalPilot 项目的增强版数据生成器，支持两级分类体系和更完整的业务指标。

## 主要特性

### 1. 时间范围
- **开始日期**: 2024-01-01
- **结束日期**: 2026-07-12
- **总天数**: 913 天

### 2. 分类体系
- **L1 分类**: 20 个顶级分类
- **L2 分类**: 81 个子分类
- **分类 ID**: 使用固定 ID（如 1001 Electronics, 100101 Phones）

### 3. 站点
10 个国际站点：US, DE, UK, AU, FR, IT, ES, CA, CN, JP

### 4. 数据表

#### daily_metrics (核心业务指标)
- **字段**: date, site, category_l1, category_l2, category_id_l1, category_id_l2, gmv, sold_items, live_listings, str, impressions, clicks, orders, ctr, cvr, asp, active_sellers, new_listings
- **数据量**: 约 50-70 万行
- **KPI 逻辑**:
  - `GMV = ASP × Sold Items`
  - `STR = Sold Items / Live Listings` (5%-30%)
  - `Clicks = Impressions × CTR`
  - `Orders = Clicks × CVR`
  - `Live Listings ≈ Impressions` (相对稳定)

#### inventory_daily (库存指标)
- **字段**: date, site, category_id_l1, category_l1, category_id_l2, category_l2, live_listings, available_inventory, out_of_stock_rate, days_of_supply, restock_qty, inventory_health
- **数据量**: 与 daily_metrics 相同
- **计算逻辑**:
  - `Available Inventory = Live Listings × (1-10)`
  - `Days of Supply = Available Inventory / Sold Items`
  - `Inventory Health = Low/Healthy/Excess` (基于 Days of Supply)

#### seller_daily_metrics (卖家级别指标)
- **字段**: date, site, category_id_l1, category_l1, category_id_l2, category_l2, seller_id, seller_name, gmv, sold_items, orders, asp, impressions, clicks, ctr, cvr, seller_share, seller_rank
- **数据量**: 约 300-500 万行
- **分配逻辑**: Top-down 分配
  - 每个 (site, category_l2) 有 5-10 个卖家
  - 卖家 GMV 汇总 = daily_metrics GMV（确保数据一致性）
  - 按市场份额分配 GMV、Sold Items、Orders 等指标

#### campaigns (促销活动)
- **字段**: campaign_id, campaign_name, site, category_id_l1, category_l1, category_id_l2, category_l2, start_date, end_date, discount_rate, subsidy_budget, target_gmv, actual_gmv, roi
- **数据量**: 约 50-100 个活动
- **活动类型**: Black Friday, Cyber Monday, Christmas, 春节等

#### sellers (卖家信息)
- **字段**: seller_id, seller_name, site, country, join_date, feedback_score, is_top_rated, status, last_listing_date
- **数据量**: 1000 个卖家
- **状态**: 90% active, 5% suspended, 5% churned

## 使用方法

### 运行脚本

```bash
cd /d/git/business-signal-pilot/data
python generate_data_v2.py
```

### 预计运行时间

- **daily_metrics**: 2-3 分钟
- **inventory_daily**: 1-2 分钟
- **seller_daily_metrics**: 5-10 分钟（数据量最大）
- **campaigns & sellers**: < 1 分钟
- **总计**: 约 10-15 分钟

### 生成的文件

```
data/signal.db  (约 50-100 MB)
```

## KPI 生成逻辑详解

### 1. 基础指标生成

```python
# 每个 (site, category_l2) 有基线指标
baseline = {
    'live_listings': 5000-50000,        # 在线商品数
    'str': 5%-30%,                      # 售罄率（因分类而异）
    'asp': 根据分类设置,                 # 平均售价
    'ctr': 1.5%-4.5%,                   # 点击率
    'cvr': 2.5%-7.5%,                   # 转化率
}
```

### 2. 衍生指标计算

```python
# Step 1: 计算销售量
sold_items = live_listings × str

# Step 2: 计算 GMV
gmv = asp × sold_items

# Step 3: 计算流量指标
impressions = live_listings × (0.8-1.2)  # 流量与库存相关
clicks = impressions × ctr
orders = clicks × cvr
```

### 3. 季节性效应

- **周末**: 流量 +20%
- **Q4 (11-12月)**: 流量和销量 +50%
- **春节 (1-2月)**: 流量和销量 +30%

### 4. 异常注入

5% 的数据点包含异常：
- **Traffic Drop**: 流量骤降 30-50%
- **Conversion Drop**: 转化率下降 30-40%
- **Spike**: 异常增长 50-100%

## 数据验证

运行脚本后，会输出数据摘要：

```
[SUMMARY] 数据生成摘要
============================================================
daily_metrics:        500,000+ 行
  日期范围:           2024-01-01 到 2026-07-12
  站点数:             10
  L1 分类数:          20
  L2 分类数:          81
  总 GMV:             $XX,XXX,XXX,XXX.XX

inventory_daily:      500,000+ 行
seller_daily_metrics: 3,000,000+ 行
  唯一卖家数:         4,000+

campaigns:            50-100 个活动
sellers:              1,000 个卖家
```

## 数据完整性保证

### Top-down 一致性

```sql
-- 验证：seller_daily_metrics 的 GMV 汇总应等于 daily_metrics
SELECT 
    dm.date, 
    dm.site, 
    dm.category_id_l2,
    dm.gmv as daily_gmv,
    SUM(sdm.gmv) as seller_total_gmv,
    ABS(dm.gmv - SUM(sdm.gmv)) as diff
FROM daily_metrics dm
LEFT JOIN seller_daily_metrics sdm 
    ON dm.date = sdm.date 
    AND dm.site = sdm.site 
    AND dm.category_id_l2 = sdm.category_id_l2
GROUP BY dm.date, dm.site, dm.category_id_l2, dm.gmv
HAVING diff > 0.01
LIMIT 10;
-- 应该返回空结果或差异极小
```

### 业务逻辑验证

```sql
-- 验证：GMV = ASP × Sold Items
SELECT 
    date, site, category_l2,
    gmv, asp, sold_items,
    (asp * sold_items) as calculated_gmv,
    ABS(gmv - (asp * sold_items)) as diff
FROM daily_metrics
WHERE ABS(gmv - (asp * sold_items)) > 1
LIMIT 10;
-- 差异应小于 1 美元（四舍五入误差）
```

## 下一步

数据生成完成后：

1. **启动后端服务**
   ```bash
   cd backend
   uvicorn app.main:app --reload
   ```

2. **测试 SQL Agent**
   ```bash
   curl -X POST http://localhost:8000/api/chat \
     -H "Content-Type: application/json" \
     -d '{"message": "US站 Phones 分类最近7天的 GMV 趋势"}'
   ```

3. **启动前端**
   ```bash
   cd frontend
   pnpm dev
   ```

## 故障排查

### 问题：内存不足
**解决方案**: 
- 减少 `seller_daily_metrics` 中每个分类的卖家数（第 424 行）
- 或者分批生成数据

### 问题：数据库锁定
**解决方案**: 
- 确保没有其他进程在使用 `signal.db`
- 删除旧的 `signal.db` 文件后重新运行

### 问题：生成时间过长
**解决方案**: 
- 减少时间范围（修改 `END_DATE`）
- 减少分类数量（注释掉部分 L1 分类）
- 降低每天生成的分类比例（第 270 行）

## 与原版 generate_data.py 的区别

| 特性 | generate_data.py | generate_data_v2.py |
|------|------------------|---------------------|
| 分类体系 | 单层（30 个分类） | 两层（20 L1 + 81 L2） |
| 分类 ID | 无固定 ID | 固定 ID（1001, 100101 等） |
| 数据表 | 3 个表 | 5 个表 |
| KPI 逻辑 | 简化逻辑 | 严格业务逻辑（GMV=ASP×SI） |
| Seller 数据 | 无 | Top-down 分配，确保一致性 |
| 库存数据 | 无 | inventory_daily 表 |
| 数据量 | ~20 万行 | ~500 万行 |
| 适用场景 | Demo/原型 | 完整的分析和诊断 |

## 技术细节

- **Python 版本**: 3.11+
- **依赖**: duckdb
- **编码**: UTF-8（Windows 兼容）
- **数据类型**: 使用 DECIMAL 确保精度
- **索引**: 自动创建日期和分类索引

## 作者

SignalPilot Team - 2026-07-15
