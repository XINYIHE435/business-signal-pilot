# SignalPilot Development Plan

**Version:** 1.0
**Timeline:** 3 Weeks Sprint
**Team Size:** 1 (Full-stack AI Engineer)

---

## Executive Summary

这份开发计划将 SignalPilot 从 0 到 MVP 的过程拆解为 3 个 week sprint，每周有清晰的交付物和里程碑。

**总体目标：** 在 3 周内交付一个可演示的 AI 驱动业务诊断平台。

---

## Week 1: MVP Foundation (核心能力搭建)

**Goal:** 建立技术基座，实现核心功能闭环

### Day 1-2: 数据层 + 后端基础

#### **Milestone 1.1: Synthetic Data Generation**

**Tasks:**

- [ ] 创建数据生成脚本 `data/generate_data.py`
  - [ ] 生成 `daily_metrics` 表（730 天 × 10 站点 × 30 品类 = 219k 行）
  - [ ] 生成 `campaigns` 表（~50 个活动）
  - [ ] 生成 `sellers` 表（~500 个卖家）
  - [ ] 注入 5 种异常模式：
    - Traffic drop（流量骤降）
    - Conversion issue（转化率下降）
    - Campaign overlap（促销重叠）
    - Seller churn（卖家流失）
    - Seasonality spike（季节性波动）

**Validation:**
```bash
python data/generate_data.py
duckdb data/signal.db -c "SELECT COUNT(*) FROM daily_metrics"
# Expected: ~220000
```

**Output:** `data/signal.db` (DuckDB 文件)

---

#### **Milestone 1.2: FastAPI Backend Setup**

**Tasks:**

- [ ] 初始化 FastAPI 项目结构
  ```bash
  cd backend
  poetry init
  poetry add fastapi uvicorn duckdb polars anthropic pydantic-settings
  ```

- [ ] 创建核心文件：
  - [ ] `backend/app/main.py` - FastAPI app
  - [ ] `backend/app/core/config.py` - 环境变量配置
  - [ ] `backend/app/core/database.py` - DuckDB 连接
  - [ ] `backend/app/models/schemas.py` - Pydantic models

- [ ] 实现第一个 API：
  ```python
  @app.get("/api/v1/health")
  async def health_check():
      return {"status": "ok", "db_connection": test_db()}
  ```

**Validation:**
```bash
uvicorn app.main:app --reload
curl http://localhost:8000/api/v1/health
```

---

### Day 3-4: Dashboard API + 前端基础

#### **Milestone 1.3: Dashboard API**

**Tasks:**

- [ ] 实现 `/api/v1/dashboard/kpis` 接口
  - [ ] 返回核心 KPI 卡片数据（GMV, SI, CTR, CVR, ASP）
  - [ ] 支持 site/category 筛选
  - [ ] 计算 WoW 变化百分比

- [ ] 实现 `/api/v1/dashboard/trends` 接口
  - [ ] 返回过去 30 天的趋势数据
  - [ ] 使用 Polars 进行聚合查询

- [ ] 实现 `/api/v1/dashboard/anomalies` 接口
  - [ ] 简单的异常检测算法（Z-score）
  - [ ] 标记超过 2σ 的异常点

**Example Response:**
```json
{
  "kpis": [
    {
      "name": "GMV",
      "value": 12345678,
      "change_percent": 5.2,
      "trend": "up"
    }
  ],
  "trends": {
    "dates": ["2027-01-01", ...],
    "gmv": [123000, 145000, ...]
  },
  "anomalies": [
    {
      "date": "2027-01-10",
      "metric": "gmv",
      "severity": "high"
    }
  ]
}
```

---

#### **Milestone 1.4: Frontend Setup + Dashboard Page**

**Tasks:**

- [ ] 初始化 Next.js 项目
  ```bash
  npx create-next-app@latest frontend --app --tailwind --typescript
  cd frontend
  pnpm add @radix-ui/react-slot class-variance-authority clsx tailwind-merge
  pnpm add lucide-react recharts
  ```

- [ ] 安装 shadcn/ui 组件
  ```bash
  npx shadcn-ui@latest init
  npx shadcn-ui@latest add card button select badge
  ```

- [ ] 创建 Dashboard 页面
  - [ ] `app/(dashboard)/page.tsx` - 主页
  - [ ] `components/KPICard.tsx` - KPI 卡片组件
  - [ ] `components/TrendChart.tsx` - 趋势图（使用 Recharts）
  - [ ] `components/AnomalyAlert.tsx` - 异常提示

- [ ] API 客户端
  - [ ] `lib/api.ts` - Fetch wrapper

**Validation:**
- Dashboard 能显示实时 KPI
- 趋势图正确渲染
- 异常点被红色高亮

---

### Day 5-7: AI Chat 基础功能

#### **Milestone 1.5: SQL Generation Agent**

**Tasks:**

- [ ] 创建 `backend/app/agents/sql_agent.py`
  - [ ] 使用 Claude function calling 生成 SQL
  - [ ] Schema awareness（知道表结构）
  - [ ] Query validation（防止危险操作）

- [ ] 实现 `/api/v1/chat/query` 接口
  - [ ] 接收自然语言查询
  - [ ] 调用 SQL Agent 生成查询
  - [ ] 执行 SQL 并返回结果

**Example Flow:**
```python
# User: "过去 7 天德国站的 GMV"
sql = await sql_agent.generate(
    query="过去 7 天德国站的 GMV",
    schema=db_schema
)
# SQL: SELECT date, SUM(gmv) FROM daily_metrics WHERE ...
result = execute_query(sql)
return format_response(result)
```

---

#### **Milestone 1.6: Chat UI**

**Tasks:**

- [ ] 创建 `app/chat/page.tsx`
- [ ] 实现聊天界面组件
  - [ ] `components/ChatInterface.tsx` - 主容器
  - [ ] `components/MessageBubble.tsx` - 消息气泡
  - [ ] `components/ChartRenderer.tsx` - 图表渲染

- [ ] 预设示例问题
  ```typescript
  const EXAMPLE_QUERIES = [
    "德国站 GMV 趋势如何？",
    "哪个品类表现最好？",
    "上周有什么异常？"
  ]
  ```

**Validation:**
- 用户输入问题后能得到答案
- 返回的数据自动渲染为图表
- 加载状态显示（骨架屏）

---

### Week 1 Deliverables

- ✅ DuckDB 数据库包含 ~220k 行数据
- ✅ FastAPI 后端运行在 localhost:8000
- ✅ Next.js 前端运行在 localhost:3000
- ✅ Dashboard 页面可用
- ✅ Ask AI 页面可用（基础版）
- ✅ 能回答简单的查询问题

**Demo Script:**
1. 打开 Dashboard，看到 KPI 和趋势图
2. 点击异常点，跳转到 Diagnosis（未实现，下周做）
3. 进入 Ask AI，问"德国站 GMV 如何？"
4. 得到答案和图表

---

## Week 2: AI Enhancement (智能诊断能力)

**Goal:** 实现核心差异化功能 - AI 根因诊断

### Day 8-10: Diagnosis Agent

#### **Milestone 2.1: Anomaly Detection**

**Tasks:**

- [ ] 实现 `backend/app/utils/anomaly_detection.py`
  - [ ] Z-score 方法（简单版）
  - [ ] Moving average 检测（中级版）
  - [ ] 可选：Prophet 时间序列预测（高级版）

- [ ] 创建异常检测 API
  ```python
  @app.post("/api/v1/diagnosis/detect")
  async def detect_anomalies(request: DetectRequest):
      anomalies = detect(
          metric=request.metric,
          site=request.site,
          date_range=request.date_range
      )
      return anomalies
  ```

---

#### **Milestone 2.2: Contribution Analysis**

**Tasks:**

- [ ] 实现 `backend/app/utils/contribution_analysis.py`
  - [ ] 维度拆解（Site / Category / Seller）
  - [ ] 计算贡献度百分比
  - [ ] Waterfall chart 数据格式

**Algorithm:**
```python
def analyze_contribution(metric, base_period, compare_period):
    base = query_metric(base_period)
    compare = query_metric(compare_period)
    delta = compare - base

    # 拆解到各个维度
    contributions = []
    for dimension in ['site', 'category']:
        dim_delta = query_by_dimension(dimension, base_period, compare_period)
        contributions.append({
            'dimension': dimension,
            'values': dim_delta,
            'contribution_percent': dim_delta / delta
        })

    return contributions
```

---

#### **Milestone 2.3: Root Cause Diagnosis Agent**

**Tasks:**

- [ ] 创建 `backend/app/agents/diagnosis_agent.py`
- [ ] 实现假设生成器
  ```python
  HYPOTHESIS_TEMPLATES = [
      {
          "type": "traffic_drop",
          "check": lambda: impressions_change < -0.2,
          "evidence_query": "SELECT ... FROM daily_metrics WHERE ..."
      },
      {
          "type": "conversion_issue",
          "check": lambda: cvr_change < -0.1,
          "evidence_query": "..."
      }
  ]
  ```

- [ ] 使用 LLM 合成诊断报告
  ```python
  async def generate_diagnosis(anomaly):
      contributions = analyze_contribution(anomaly)
      hypotheses = generate_hypotheses(contributions)
      evidence = await collect_evidence(hypotheses)

      prompt = f"""
      Based on the following data:
      - Metric: {anomaly.metric} dropped by {anomaly.change}%
      - Contributions: {contributions}
      - Evidence: {evidence}

      Provide a clear diagnosis report with:
      1. Root cause (most likely)
      2. Supporting evidence
      3. Recommended actions
      """

      response = await claude_client.generate(prompt)
      return parse_diagnosis(response)
  ```

---

#### **Milestone 2.4: Diagnosis Page**

**Tasks:**

- [ ] 创建 `app/diagnosis/page.tsx`
- [ ] UI 组件：
  - [ ] `DiagnosisPanel.tsx` - 主面板
  - [ ] `CauseTree.tsx` - 根因树状图
  - [ ] `EvidenceCard.tsx` - 证据卡片
  - [ ] `ActionList.tsx` - 建议动作列表

**User Flow:**
```
Dashboard 点击异常
  ↓
跳转到 /diagnosis?anomaly_id=xxx
  ↓
显示 Loading... (AI 诊断中)
  ↓ (5-10秒)
显示诊断报告
```

---

### Day 11-12: Report Generation

#### **Milestone 2.5: Report Generator**

**Tasks:**

- [ ] 创建 `backend/app/utils/report_generator.py`
- [ ] 实现报告模板
  ```python
  REPORT_TEMPLATE = """
  # Weekly Business Report
  **Period:** {start_date} to {end_date}

  ## Executive Summary
  {executive_summary}

  ## Site Performance
  {site_table}

  ## Key Findings
  {findings}

  ## Recommended Actions
  {actions}
  """
  ```

- [ ] 使用 LLM 生成 Executive Summary
  ```python
  async def generate_executive_summary(kpis, anomalies):
      prompt = f"""
      Based on this week's data:
      - GMV: {kpis.gmv} ({kpis.gmv_change}%)
      - Key anomalies: {anomalies}

      Write a 2-3 sentence executive summary.
      """
      return await llm.generate(prompt)
  ```

- [ ] API 接口
  ```python
  @app.post("/api/v1/report/generate")
  async def generate_report(request: ReportRequest):
      report = await generate_weekly_report(
          start_date=request.start_date,
          end_date=request.end_date,
          sites=request.sites
      )
      return {"report_id": report.id, "content": report.markdown}
  ```

---

#### **Milestone 2.6: Report Page**

**Tasks:**

- [ ] 创建 `app/report/page.tsx`
- [ ] Markdown 渲染（使用 `react-markdown`）
- [ ] 导出功能（Markdown / PDF）
- [ ] 历史报告列表

---

### Day 13-14: Multi-turn Conversation

#### **Milestone 2.7: Conversation Context**

**Tasks:**

- [ ] 实现对话历史管理
  ```python
  class ConversationManager:
      def __init__(self):
          self.sessions = {}

      def add_message(self, session_id, role, content):
          if session_id not in self.sessions:
              self.sessions[session_id] = []
          self.sessions[session_id].append({
              "role": role,
              "content": content
          })

      def get_context(self, session_id, max_turns=5):
          return self.sessions.get(session_id, [])[-max_turns:]
  ```

- [ ] 修改 Chat API 支持上下文
  ```python
  @app.post("/api/v1/chat/query")
  async def chat_query(request: ChatRequest):
      context = conv_manager.get_context(request.session_id)
      response = await orchestrator.process(
          query=request.query,
          context=context
      )
      conv_manager.add_message(request.session_id, "assistant", response)
      return response
  ```

**Example Flow:**
```
User: "德国站 GMV 如何？"
AI: "德国站上周 GMV 下降了 15%"

User: "为什么？"  # 能理解这是在问上一个问题的原因
AI: "主要因为转化率下降..."
```

---

### Week 2 Deliverables

- ✅ Diagnosis Agent 能正确诊断异常
- ✅ Diagnosis 页面可用
- ✅ Report 自动生成
- ✅ Report 页面可用
- ✅ Chat 支持多轮对话

**Demo Script:**
1. Dashboard 发现德国站 GMV 异常
2. 点击进入 Diagnosis，AI 自动诊断根因
3. 查看诊断报告，看到 3 个假设 + 证据
4. 进入 Ask AI，追问"如果增加补贴会怎样？"
5. 生成 Weekly Report，导出为 Markdown

---

## Week 3: Demo Polish (产品化打磨)

**Goal:** 让产品看起来像真实的 SaaS 产品

### Day 15-16: UI/UX Refinement

#### **Milestone 3.1: Design System**

**Tasks:**

- [ ] 统一配色方案
  ```typescript
  // tailwind.config.ts
  theme: {
    colors: {
      brand: {
        50: '#f0f9ff',
        500: '#3b82f6',
        900: '#1e3a8a'
      }
    }
  }
  ```

- [ ] 统一组件样式
  - [ ] 所有卡片统一圆角、阴影
  - [ ] 所有按钮统一高度、间距
  - [ ] 统一字体（Inter / SF Pro）

- [ ] 添加微交互
  - [ ] Hover 效果
  - [ ] 页面切换动画（Framer Motion）
  - [ ] Loading skeleton

---

#### **Milestone 3.2: Data Visualization Polish**

**Tasks:**

- [ ] 替换 Recharts 为 Plotly（更专业）
- [ ] 统一图表配色
- [ ] 添加 Tooltip
- [ ] 添加 Annotation（标注异常点）

**Example:**
```typescript
const chartConfig = {
  layout: {
    font: { family: 'Inter' },
    plot_bgcolor: '#f9fafb',
    paper_bgcolor: '#ffffff'
  },
  annotations: anomalies.map(a => ({
    x: a.date,
    y: a.value,
    text: '⚠️ Anomaly',
    showarrow: true
  }))
}
```

---

#### **Milestone 3.3: Loading & Error States**

**Tasks:**

- [ ] 统一 Loading 状态
  ```tsx
  {isLoading ? (
    <Skeleton className="h-[200px] w-full" />
  ) : (
    <Chart data={data} />
  )}
  ```

- [ ] 错误处理
  ```tsx
  {error ? (
    <Alert variant="destructive">
      <AlertTitle>加载失败</AlertTitle>
      <AlertDescription>{error.message}</AlertDescription>
    </Alert>
  ) : null}
  ```

- [ ] Empty state
  ```tsx
  {data.length === 0 ? (
    <EmptyState
      icon={<Inbox />}
      title="暂无数据"
      description="选择不同的筛选条件试试"
    />
  ) : (
    <DataTable data={data} />
  )}
  ```

---

### Day 17-18: Performance & Testing

#### **Milestone 3.4: Performance Optimization**

**Tasks:**

- [ ] Frontend 优化
  - [ ] 代码分割（动态导入）
  ```tsx
  const Chart = dynamic(() => import('./Chart'), { ssr: false })
  ```
  - [ ] 图片优化（Next.js Image）
  - [ ] API 请求去重（SWR）

- [ ] Backend 优化
  - [ ] SQL 查询缓存
  ```python
  from functools import lru_cache

  @lru_cache(maxsize=100)
  def get_kpis(site, date):
      return query_db(...)
  ```
  - [ ] 并行执行 Tools
  ```python
  results = await asyncio.gather(
      tool1.run(),
      tool2.run(),
      tool3.run()
  )
  ```

**Target Metrics:**
- Dashboard 首屏加载 < 2s
- API 响应时间 < 1s
- AI 诊断 < 10s

---

#### **Milestone 3.5: Testing**

**Tasks:**

- [ ] Backend 单元测试
  ```python
  # tests/test_sql_agent.py
  def test_sql_generation():
      sql = sql_agent.generate("过去 7 天的 GMV")
      assert "SUM(gmv)" in sql
      assert "7 DAY" in sql
  ```

- [ ] API 集成测试
  ```python
  def test_dashboard_kpis():
      response = client.get("/api/v1/dashboard/kpis")
      assert response.status_code == 200
      assert "gmv" in response.json()["kpis"]
  ```

- [ ] Frontend E2E 测试（Playwright）
  ```typescript
  test('user can ask AI question', async ({ page }) => {
    await page.goto('/chat')
    await page.fill('textarea', '德国站 GMV 如何？')
    await page.click('button[type=submit]')
    await expect(page.locator('.response')).toBeVisible()
  })
  ```

---

### Day 19-20: Deployment & Documentation

#### **Milestone 3.6: Deployment**

**Tasks:**

- [ ] 前端部署到 Vercel
  ```bash
  cd frontend
  vercel --prod
  ```

- [ ] 后端部署到 Fly.io
  ```bash
  cd backend
  fly launch
  fly deploy
  ```

- [ ] 环境变量配置
  ```bash
  # Vercel
  NEXT_PUBLIC_API_URL=https://api.signalpilot.fly.dev

  # Fly.io
  fly secrets set ANTHROPIC_API_KEY=sk-xxx
  fly secrets set DATABASE_URL=/data/signal.db
  ```

- [ ] 上传 DuckDB 文件到 Fly.io Volume
  ```bash
  fly volumes create signal_data --size 1
  fly sftp shell
  put data/signal.db /data/signal.db
  ```

---

#### **Milestone 3.7: Documentation**

**Tasks:**

- [ ] 更新 README.md
  - [ ] 项目介绍
  - [ ] 功能截图
  - [ ] 快速开始
  - [ ] 技术栈

- [ ] 创建 API 文档
  - [ ] 使用 FastAPI 自动生成
  - [ ] 访问 `/docs` 查看

- [ ] 录制 Demo 视频（3 分钟）
  - [ ] 场景 1: Dashboard 监控
  - [ ] 场景 2: AI 诊断异常
  - [ ] 场景 3: 自然语言查询
  - [ ] 场景 4: 生成报告

---

#### **Milestone 3.8: Demo Polish**

**Tasks:**

- [ ] 准备演示数据
  - [ ] 确保有明显的异常点
  - [ ] 准备 5 个示例问题

- [ ] Landing Page（可选）
  - [ ] 简单的产品介绍页
  - [ ] "Try Demo" 按钮

- [ ] Case Study（可选）
  - [ ] 写一个虚构的案例
  - [ ] "eBay 德国站 GMV 下降 15% 诊断案例"

---

### Day 21: Final Review & Launch

#### **Milestone 3.9: Quality Assurance**

**Checklist:**

- [ ] 所有 4 个页面都能正常访问
- [ ] Dashboard 显示正确的 KPI
- [ ] Diagnosis 能诊断异常
- [ ] Ask AI 能回答至少 10 个预设问题
- [ ] Report 生成成功
- [ ] 移动端基本可用（Responsive）
- [ ] 错误处理优雅
- [ ] Loading 状态友好
- [ ] API 文档完整
- [ ] README 清晰

---

#### **Milestone 3.10: Launch**

**Tasks:**

- [ ] 部署到生产环境
- [ ] 分享 Demo 链接
  - [ ] GitHub README
  - [ ] LinkedIn post
  - [ ] Product Hunt (optional)

- [ ] 准备面试 Demo Script
  ```markdown
  ## Demo Script (5 分钟)

  ### Opening (30s)
  "Hi, this is SignalPilot, an AI-powered business diagnosis platform I built for cross-border e-commerce analytics."

  ### Dashboard (1min)
  "Let me show you the dashboard. Here we monitor key metrics across 10 sites and 30 categories. Notice this red alert? That's an anomaly detected by our AI."

  ### Diagnosis (2min)
  "Click on the anomaly, and our AI agent automatically diagnoses the root cause. It does contribution analysis, generates hypotheses, and collects evidence. In this case, it identified a logistics delay causing conversion drop."

  ### Ask AI (1.5min)
  "Now, I can ask questions in natural language. 'Why did Germany GMV drop?' The AI generates SQL, queries the database, and explains the finding. I can follow up: 'What if we increase subsidy by 10%?' It runs a simulation."

  ### Report (30s)
  "Finally, it generates a weekly business review automatically, saving hours of manual work."

  ### Closing (30s)
  "The entire stack is Next.js + FastAPI + DuckDB + Claude API. All data is synthetic, designed to mimic real eBay analytics workflows. Happy to dive into the technical details!"
  ```

---

### Week 3 Deliverables

- ✅ 产品级 UI/UX
- ✅ 性能优化完成
- ✅ 测试覆盖核心路径
- ✅ 部署到生产环境
- ✅ 文档完整
- ✅ Demo 视频录制
- ✅ 准备好面试演示

---

## Summary: 3-Week Roadmap

| Week | Focus | Key Deliverables |
|------|-------|------------------|
| **Week 1** | Foundation | 数据 + API + Dashboard + Chat |
| **Week 2** | AI Enhancement | Diagnosis + Report + Context |
| **Week 3** | Demo Polish | UI + Performance + Deploy |

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| DuckDB 性能不足 | 预聚合 + 缓存层 |
| LLM 回答不准确 | 提供数据源引用 + 人工审核模式 |
| API 成本过高 | Prompt caching + 结果缓存 |
| 时间不足 | 砍掉 What-if simulation |

---

## Success Criteria

**必须达成：**
- [ ] 4 个页面全部可用
- [ ] AI 能正确回答 80% 的预设问题
- [ ] Dashboard 加载 < 3s
- [ ] 部署链接可公开访问

**加分项：**
- [ ] 获得 3+ 个真实分析师的正面反馈
- [ ] 被 Product Hunt 收录
- [ ] GitHub stars > 50

---

## Post-Launch (Week 4+)

**可能的优化方向：**

1. **性能优化**
   - 迁移到 PostgreSQL + TimescaleDB
   - 实现 Redis 缓存层

2. **功能增强**
   - What-if simulation
   - 实时告警（Slack/Email）
   - 自定义 Dashboard

3. **AI 升级**
   - Fine-tune 专属模型
   - Multi-agent collaboration
   - 自动执行运营动作

4. **产品化**
   - 用户系统 + 权限管理
   - 团队协作
   - 移动端 App

---

**Next Action:**

现在开始 Week 1 Day 1 的第一个任务：生成合成数据！

---

*Last updated: 2027-01-15*
