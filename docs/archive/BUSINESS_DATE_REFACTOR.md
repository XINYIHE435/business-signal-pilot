# 业务日期（Business Date）系统重构

## 问题背景

之前系统使用服务器当前时间（`datetime.now()` / `date.today()`）作为基准日期，导致：
- 数据库数据更新到 2026-07-12，但系统时间是 2026-07-16
- "Last 7 Days" 查询 2026-07-09 到 2026-07-16，但数据库只有到 2026-07-12
- 查询结果为空或不完整
- 每次数据更新后需要手动调整代码

## 解决方案

**核心思想**: 所有日期计算基于数据库的最大日期（Business Date），而非系统时间。

### 架构变更

```
旧逻辑:
  System Time (2026-07-16) → Last 7 Days → Query [2026-07-09 to 2026-07-16] → 空结果

新逻辑:
  DB MAX(date) (2026-07-12) → Last 7 Days → Query [2026-07-05 to 2026-07-12] → 完整数据
```

## 修改内容

### 1. Backend - 数据库层

**文件**: `backend/app/core/database_v2.py`

新增方法：
```python
def get_max_date(self):
    """
    获取数据库中的最大业务日期（Business Date）
    
    Returns:
        date: 数据库中最新的业务日期
    """
    try:
        result = self.execute("SELECT MAX(date) FROM daily_metrics")
        if result and result[0][0]:
            max_date = result[0][0]
            logger.info("max_date_fetched", max_date=str(max_date))
            return max_date
        else:
            logger.warning("no_data_in_daily_metrics")
            return None
    except Exception as e:
        logger.error("failed_to_get_max_date", error=str(e))
        return None
```

### 2. Backend - API 层

**文件**: `backend/app/api/dashboard_v2.py`

#### 2.1 新增 Business Date 端点

```python
@router.get("/business-date")
async def get_business_date():
    """获取当前业务日期（数据库中的最大日期）"""
    try:
        business_date = db_v2.get_max_date()
        if not business_date:
            raise HTTPException(status_code=500, detail="No data available in database")
        
        return {
            "business_date": str(business_date),
            "description": "Latest available data date"
        }
    except Exception as e:
        logger.error("business_date_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch business date: {str(e)}")
```

#### 2.2 修改所有端点的日期计算

**修改前**:
```python
end_date = datetime.now().date()
start_date = end_date - timedelta(days=days)
```

**修改后**:
```python
# 获取数据库中的最大业务日期
end_date = db_v2.get_max_date()
if not end_date:
    raise HTTPException(status_code=500, detail="No data available in database")

start_date = end_date - timedelta(days=days)
```

受影响的端点：
- `/api/v1/dashboard/kpis` - KPI 数据
- `/api/v1/dashboard/trends` - 趋势数据
- `/api/v1/dashboard/anomalies` - 异常检测

## 测试验证

### 1. 检查当前业务日期

```bash
curl http://localhost:8000/api/v1/dashboard/business-date
```

预期返回：
```json
{
  "business_date": "2026-07-12",
  "description": "Latest available data date"
}
```

### 2. 验证日期范围

```bash
# Last 7 Days - 应该查询 2026-07-05 到 2026-07-12
curl "http://localhost:8000/api/v1/dashboard/kpis?site=US&days=7"

# 检查返回的 date_range 字段
# 预期: "2026-07-05 to 2026-07-12"
```

### 3. 验证 SQL 查询

手动查询数据库验证：
```sql
-- 检查最大日期
SELECT MAX(date) FROM daily_metrics;
-- 结果: 2026-07-12

-- 验证 Last 7 Days 数据存在
SELECT COUNT(*) FROM daily_metrics 
WHERE date >= '2026-07-05' AND date <= '2026-07-12';
-- 应该有数据
```

## 优势

### 1. 自动适配
- 数据库更新到任何日期，系统自动跟随
- 无需修改代码

### 2. 数据完整性
- 查询范围永远在数据库范围内
- 不会出现空结果

### 3. 一致性
- 所有 API 端点使用统一的业务日期基准
- Dashboard、SQL Agent、Reports 保持同步

### 4. 可测试性
- 可以通过修改数据库日期范围来测试不同场景
- 不依赖系统时间

## 日志示例

系统启动时会记录：
```
[info] max_date_fetched max_date=2026-07-12
[info] kpis_fetched site=US days=7 gmv=12345678.90
```

如果数据库为空：
```
[warning] no_data_in_daily_metrics
[error] business_date_fetch_failed error=No data available in database
```

## 注意事项

### 1. 缓存处理
如果使用了 Redis 或内存缓存，需要注意：
- 缓存键应该包含业务日期
- 数据库更新后需要刷新缓存

### 2. 前端显示
前端可以调用 `/business-date` 端点显示当前数据的业务日期：
```
"Data as of 2026-07-12"
```

### 3. 数据更新流程
1. 运行 `generate_data_v2.py` 更新数据到新日期
2. 重启 Backend（或自动检测）
3. 系统自动使用新的最大日期

## 未来扩展

### 1. 多数据源支持
如果有多个表（如 `seller_daily_metrics`、`inventory_daily`），需要检查所有表的最大日期：
```python
def get_max_date(self):
    """获取所有表的最大日期中的最小值（确保数据一致性）"""
    queries = [
        "SELECT MAX(date) FROM daily_metrics",
        "SELECT MAX(date) FROM seller_daily_metrics",
        "SELECT MAX(date) FROM inventory_daily"
    ]
    dates = []
    for query in queries:
        result = self.execute(query)
        if result and result[0][0]:
            dates.append(result[0][0])
    
    return min(dates) if dates else None
```

### 2. 业务日历支持
如果需要跳过周末/节假日：
```python
def get_business_date(self, skip_weekends=False):
    max_date = self.get_max_date()
    if skip_weekends:
        while max_date.weekday() >= 5:  # 5=Saturday, 6=Sunday
            max_date -= timedelta(days=1)
    return max_date
```

### 3. 时区支持
如果系统跨时区运行，需要考虑时区转换：
```python
def get_max_date(self, timezone='UTC'):
    # 返回带时区信息的日期
    pass
```

## 总结

✅ **修改完成**
- 所有 Dashboard API 端点使用业务日期
- 新增 `/business-date` 端点供前端查询
- 系统自动适配数据库日期范围

✅ **优势**
- 无需手动调整代码
- 查询结果永远完整
- 测试更容易

✅ **向后兼容**
- 现有 API 接口不变
- 只是日期计算逻辑改变
