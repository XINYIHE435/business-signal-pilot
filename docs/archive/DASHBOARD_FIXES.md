# Dashboard 前端问题修复总结

## 修复的问题

### 1. ✅ 分类筛选器失效
**问题**: Category L1/L2 筛选器调整后，KPI 和趋势图未更新

**根本原因**: 
- 前端使用了 `category_l1` 和 `category_l2` 参数
- 但 `dashboard_v2.py` API 使用单个 `category` 参数（兼容 V1/V2）

**修复内容**:
- [page.tsx:36-58](frontend/app/page.tsx#L36-L58) - 修改 API 调用逻辑
  ```typescript
  // 优先使用 L2，其次 L1
  const categoryParam = category.l2 || category.l1 || undefined
  return dashboardAPI.getKPIs({
    site,
    category: categoryParam,  // 单个参数
    days
  })
  ```
- [api.ts:40-62](frontend/lib/api.ts#L40-L62) - 修改 API 接口签名
  ```typescript
  getKPIs: (params?: { site?: string; category?: string; days?: number })
  getTrends: (params?: { site?: string; category?: string; days?: number })
  ```

### 2. ✅ 年度视图 API 报错
**问题**: Period 选择 "2024 Full Year" 时报错 `Input should be less than or equal to 90`

**根本原因**: 
- 前端请求 `days=365`
- 后端 API 校验限制 `le=90`

**修复内容**:
- [dashboard_v2.py:51](backend/app/api/dashboard_v2.py#L51) - KPI 端点
  ```python
  days: int = Query(7, description="对比天数", ge=1, le=365)  # 从 90 改为 365
  ```
- [dashboard_v2.py:178](backend/app/api/dashboard_v2.py#L178) - Trends 端点
  ```python
  days: int = Query(30, description="天数", ge=7, le=730)  # 支持 2 年
  ```
- [dashboard_v2.py:248](backend/app/api/dashboard_v2.py#L248) - Anomalies 端点
  ```python
  days: int = Query(7, description="天数", ge=1, le=365)  # 从 90 改为 365
  ```

### 3. ✅ 趋势图布局优化
**问题**: 三个图表纵向排列，占用大量滚动空间

**修复内容**:
- [page.tsx:206](frontend/app/page.tsx#L206) - 修改 grid 布局
  ```tsx
  {/* 修改前 */}
  <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-4">
  
  {/* 修改后 */}
  <div className="grid grid-cols-1 xl:grid-cols-3 gap-4">
  ```

**效果**: 
- 移动端: 1 列垂直排列
- 桌面端 (≥1280px): 3 列横向并排

### 4. ✅ 图表标题动态更新
**问题**: 切换 Period 后，图表标题显示旧的天数（如 "Last 365 Days"）

**根本原因**:
- 使用了 `trendDays` 变量（固定为 30 天或更长）
- 未与实际选择的 `days` 同步

**修复内容**:
- [page.tsx:47-56](frontend/app/page.tsx#L47-L56) - 移除 `trendDays` 逻辑
  ```typescript
  // 修改前
  const trendDays = days >= 30 ? days : 30
  getTrends({ days: trendDays })
  
  // 修改后
  getTrends({ days })  // 直接使用 days
  ```
- [page.tsx:210-224](frontend/app/page.tsx#L210-L224) - 图表标题使用 `days`
  ```tsx
  title={`GMV Trend - ${site} (Last ${days} Days)`}
  title={`ASP Trend - ${site} (Last ${days} Days)`}
  title={`STR Trend - ${site} (Last ${days} Days)`}
  ```

## 文件变更清单

### Backend
- `backend/app/api/dashboard_v2.py`
  - 第 51 行: KPI `days` 上限 90 → 365
  - 第 178 行: Trends `days` 上限 90 → 730
  - 第 248 行: Anomalies `days` 上限 90 → 365

### Frontend
- `frontend/app/page.tsx`
  - 第 36-58 行: 修改 API 调用逻辑（使用单个 category 参数）
  - 第 206 行: 优化图表布局（3 列并排）
  - 第 210-224 行: 图表标题使用动态 `days`
  
- `frontend/lib/api.ts`
  - 第 40-62 行: 修改 API 接口签名（category_l1/l2 → category）

## 测试检查清单

### 1. 分类筛选
- [ ] 选择 L1 分类（如 Electronics），KPI 卡片数据更新
- [ ] 再选择 L2 分类（如 Phones），数据进一步筛选
- [ ] 清除分类，恢复全站数据

### 2. 年度视图
- [ ] 选择 "Last 7 days"，正常显示
- [ ] 选择 "Last Quarter (90 days)"，正常显示
- [ ] 选择 "2024 Full Year"，正常显示（不报错）
- [ ] 选择 "2025 Full Year"，正常显示

### 3. 图表布局
- [ ] 桌面端 (≥1280px) 三图横向并排
- [ ] 移动端 (<1280px) 纵向堆叠

### 4. 图表标题
- [ ] 选择 "Last 7 days"，标题显示 "(Last 7 Days)"
- [ ] 切换到 "Last 30 days"，标题更新为 "(Last 30 Days)"
- [ ] 切换到 "2024 Full Year"，标题更新为 "(Last 365 Days)"

## API 端点验证

启动 Backend 后，可以直接测试：

```bash
# 测试年度视图（365 天）
curl "http://localhost:8000/api/v1/dashboard/trends?site=US&days=365"

# 测试分类筛选
curl "http://localhost:8000/api/v1/dashboard/kpis?site=DE&category=Electronics&days=7"

# 测试 L2 分类
curl "http://localhost:8000/api/v1/dashboard/trends?site=US&category=Phones&days=30"
```

所有修复已完成，可以重启 Backend 和 Frontend 进行测试！
