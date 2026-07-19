# Dashboard Report Integration - 实现总结

## 概述
在 Dashboard 页面集成了统一的 Export Report 功能，复用已有的 Report Agent Workflow，无需新增独立页面或额外 API。

## 实现内容

### 1. 后端 API（lib/api.ts）
- **新增方法**: `dashboardAPI.generateReport()`
- **端点**: `POST /api/v1/dashboard/report`（已存在，复用）
- **参数**:
  - `site`: 站点（从 Dashboard 筛选条件继承）
  - `start_date`: 开始日期（YYYY-MM-DD）
  - `end_date`: 结束日期（YYYY-MM-DD）
  - `category`: 可选，品类筛选
  - `report_type`: "monthly"

### 2. 前端 UI（app/page.tsx）

#### 新增按钮
- **位置**: Dashboard Header，位于 AI Agent 和 Refresh 按钮之间
- **图标**: FileText（紫色主题）
- **触发**: 打开 Report Modal

#### Report Modal
**输入区（未生成报告时）**:
- 显示当前筛选条件（站点、品类）
- Year 选择器（2024-2026）
- Month 选择器（1-12月）
- "生成月报"按钮（带加载状态）

**预览区（报告生成后）**:
- 报告标题和元数据
- 复用 `ReportView` 组件展示 Executive Summary
- "Download Markdown" 按钮

#### 下载功能
- **格式**: Markdown
- **文件名**: `report_{site}_{start_date}.md`
- **内容结构**:
  ```markdown
  # 业务月报
  **站点**: XX
  **时间范围**: YYYY-MM-DD ~ YYYY-MM-DD
  
  ## 概览
  ...
  
  ## 关键发现
  - ...
  
  ## 趋势
  - ...
  
  ## 建议
  - ...
  ```

### 3. 状态管理
新增 React State:
- `reportModalOpen`: Modal 开关
- `reportLoading`: 生成状态
- `reportYear/reportMonth`: 时间选择
- `reportData`: 报告数据（复用 ChatQueryResponse 的 response 字段）
- `reportError`: 错误信息

## 与 Chat 的一致性
- **共享 Workflow**: 两者调用相同的 `run_dashboard_report` / Report Agent
- **数据结构一致**: 返回相同的 `executive_summary` 结构
- **预览组件复用**: Dashboard 和 Chat 都使用 `ReportView` 组件

## 验证场景

### ✅ 已完成
1. Dashboard Header 显示 "Export Report" 按钮
2. 点击按钮打开 Modal，显示当前筛选条件
3. 可选择 Year + Month
4. 调用 `/api/v1/dashboard/report` API
5. 报告生成后在 Modal 内预览（ReportView）
6. 提供 Download Markdown 按钮
7. TypeScript 编译通过

### 🔄 待实际运行验证
1. 点击 "Export Report"，选择 2026年6月（或当前有数据的月份），生成月报
2. 验证 Dashboard 和 Chat 生成的报告内容一致（相同站点、时间范围）

## 文件变更
- `frontend/lib/api.ts`: +32 行（新增 generateReport API）
- `frontend/app/page.tsx`: +118 行（按钮、Modal、逻辑）
- `backend/app/api/dashboard_v2.py`: 已有端点，无需修改

## UI 风格
- 紫色主题（Purple-600）与其他功能区分
- Modal 设计与 Diagnosis Modal 保持一致
- 响应式布局，支持 max-h-[90vh] 滚动

## 技术亮点
1. **零新增 API**: 完全复用已有的 Report Workflow
2. **轻量级集成**: 无需独立路由或页面
3. **状态隔离**: Report Modal 与 Diagnosis Modal 独立管理
4. **一键下载**: 前端直接生成 Markdown，无需后端参与
