# SignalPilot Technical Architecture

**Version:** 1.0
**Last Updated:** 2027-01-15
**Status:** Design Review

---

## 1. System Overview

### 1.1 Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                         Frontend Layer                       │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Next.js 14 (App Router) + React + Tailwind + shadcn│   │
│  └──────────────────────────────────────────────────────┘   │
│    │ Dashboard │ Diagnosis │ Ask AI │ Report │              │
└─────────────────────────────────────────────────────────────┘
                              │
                         REST API / SSE
                              │
┌─────────────────────────────────────────────────────────────┐
│                         Backend Layer                        │
│  ┌──────────────────────────────────────────────────────┐   │
│  │              FastAPI (Python 3.11+)                  │   │
│  │                                                      │   │
│  │  ├─ API Routes                                      │   │
│  │  ├─ AI Agent Orchestrator                          │   │
│  │  ├─ Query Engine (DuckDB + Polars)                 │   │
│  │  └─ LLM Integration (Claude/OpenAI)                │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │                   │
          ┌─────────▼────────┐  ┌──────▼────────┐
          │   DuckDB          │  │  Claude API   │
          │  (Embedded DB)    │  │  / OpenAI API │
          │                   │  │               │
          │ • daily_metrics   │  └───────────────┘
          │ • campaigns       │
          │ • sellers         │
          └───────────────────┘
```

### 1.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **Frontend** | Next.js 14 (App Router) | SSR + RSC + 最佳 DX |
| **UI** | Tailwind + shadcn/ui | 快速开发 + 美观一致 |
| **Visualization** | Plotly.js | 交互式图表 |
| **Backend** | FastAPI | 异步支持 + AI 友好 |
| **Data Processing** | Polars | 比 Pandas 快 10x |
| **Database** | DuckDB | 嵌入式 OLAP，无需部署 |
| **AI** | Claude 3.5 Sonnet | Function calling 稳定 |
| **Deploy** | Vercel (Frontend) + Modal/Fly.io (Backend) | Serverless 弹性 |

---

## 2. Data Architecture

### 2.1 Database Schema

#### **Table: daily_metrics**

核心业务指标表（模拟 eBay 的 daily rollup）

```sql
CREATE TABLE daily_metrics (
  date DATE NOT NULL,
  site VARCHAR NOT NULL,              -- US, DE, UK, AU, etc.
  category VARCHAR NOT NULL,          -- Electronics, Fashion, Home, etc.
  gmv DECIMAL(15, 2),                 -- Gross Merchandise Value
  sold_items INTEGER,                 -- SI (Sold Items)
  impressions INTEGER,
  clicks INTEGER,
  orders INTEGER,
  ctr DECIMAL(5, 4),                  -- Click-through Rate
  cvr DECIMAL(5, 4),                  -- Conversion Rate
  asp DECIMAL(10, 2),                 -- Average Selling Price
  active_sellers INTEGER,
  new_listings INTEGER,
  PRIMARY KEY (date, site, category)
);

-- 索引优化
CREATE INDEX idx_date ON daily_metrics(date);
CREATE INDEX idx_site_category ON daily_metrics(site, category);
```

**数据量估算：**
- Sites: 10
- Categories: 30
- Days: 730 (2 years)
- Total rows: ~220k

---

#### **Table: campaigns**

促销活动表

```sql
CREATE TABLE campaigns (
  campaign_id VARCHAR PRIMARY KEY,
  campaign_name VARCHAR NOT NULL,
  site VARCHAR NOT NULL,
  category VARCHAR,                   -- NULL = all categories
  start_date DATE NOT NULL,
  end_date DATE NOT NULL,
  discount_rate DECIMAL(5, 2),       -- e.g., 0.15 = 15% off
  subsidy_budget DECIMAL(12, 2),     -- Total subsidy amount
  target_gmv DECIMAL(15, 2),
  actual_gmv DECIMAL(15, 2),
  roi DECIMAL(5, 2)                  -- Return on Investment
);
```

---

#### **Table: sellers**

卖家基础信息

```sql
CREATE TABLE sellers (
  seller_id VARCHAR PRIMARY KEY,
  seller_name VARCHAR NOT NULL,
  site VARCHAR NOT NULL,
  country VARCHAR NOT NULL,          -- Seller location
  join_date DATE NOT NULL,
  feedback_score INTEGER DEFAULT 0,
  is_top_rated BOOLEAN DEFAULT FALSE,
  status VARCHAR DEFAULT 'active',   -- active, suspended, churned
  last_listing_date DATE
);
```

---

#### **Table: anomalies**

异常检测结果（由系统生成）

```sql
CREATE TABLE anomalies (
  id VARCHAR PRIMARY KEY,
  detected_at TIMESTAMP NOT NULL,
  date DATE NOT NULL,
  metric_name VARCHAR NOT NULL,      -- gmv, ctr, cvr, etc.
  site VARCHAR,
  category VARCHAR,
  expected_value DECIMAL(15, 2),
  actual_value DECIMAL(15, 2),
  deviation_percent DECIMAL(5, 2),
  severity VARCHAR,                  -- low, medium, high, critical
  root_cause_hypothesis TEXT,
  is_diagnosed BOOLEAN DEFAULT FALSE
);
```

---

### 2.2 Data Flow

```
┌─────────────────┐
│ Synthetic Data  │
│   Generator     │  (Python script)
└────────┬────────┘
         │
         │ Generate 1M rows
         │
         ▼
┌─────────────────┐
│   DuckDB File   │  data/signal.db
│  (500MB ~ 1GB)  │
└────────┬────────┘
         │
         │ Query via Polars/SQL
         │
         ▼
┌─────────────────┐
│  FastAPI Query  │
│     Engine      │
└────────┬────────┘
         │
         │ JSON response
         │
         ▼
┌─────────────────┐
│  Next.js UI     │
│  (Plotly Chart) │
└─────────────────┘
```

---

## 3. AI Agent Architecture

### 3.1 Agent Workflow

SignalPilot 使用 **Multi-Agent Orchestration** 模式：

```
User Query
    │
    ▼
┌─────────────────────────────────────┐
│  Orchestrator Agent                 │
│  (决策中心)                         │
│                                     │
│  1. Intent Classification           │
│  2. Task Decomposition              │
│  3. Tool Selection                  │
│  4. Response Synthesis              │
└──────────┬──────────────────────────┘
           │
           ├─────────┬─────────┬─────────┐
           │         │         │         │
           ▼         ▼         ▼         ▼
    ┌──────────┐ ┌──────┐ ┌────────┐ ┌────────┐
    │ SQL Gen  │ │ Calc │ │ Chart  │ │ Diag   │
    │ Agent    │ │Agent │ │ Agent  │ │ Agent  │
    └──────────┘ └──────┘ └────────┘ └────────┘
         │           │         │         │
         └───────────┴─────────┴─────────┘
                      │
                      ▼
              Final Response
```

---

### 3.2 Agent Types

#### **1. Orchestrator Agent**

**职责：** 理解用户意图，调度子 Agent

**Input:**
```json
{
  "query": "为什么德国站 GMV 上周下降了 15%?",
  "context": {
    "current_page": "dashboard",
    "selected_filters": {"site": "DE"}
  }
}
```

**Output:**
```json
{
  "intent": "root_cause_analysis",
  "entities": {
    "metric": "gmv",
    "site": "DE",
    "time_range": "last_week"
  },
  "plan": [
    {"agent": "sql_gen", "task": "fetch_gmv_trend"},
    {"agent": "diagnosis", "task": "analyze_drop"}
  ]
}
```

**Implementation:**
```python
class OrchestratorAgent:
    def __init__(self, llm_client):
        self.llm = llm_client
        self.tools = [SQLAgent, CalcAgent, ChartAgent, DiagnosisAgent]

    async def process(self, query: str, context: dict):
        # Step 1: Intent classification
        intent = await self.classify_intent(query)

        # Step 2: Entity extraction
        entities = await self.extract_entities(query)

        # Step 3: Generate execution plan
        plan = await self.generate_plan(intent, entities)

        # Step 4: Execute plan
        results = await self.execute_plan(plan)

        # Step 5: Synthesize response
        response = await self.synthesize(results, query)

        return response
```

---

#### **2. SQL Generation Agent**

**职责：** 将自然语言转换为 SQL

**Example:**

Input: "过去 7 天德国站 Electronics 的 GMV"

Output:
```sql
SELECT
  date,
  SUM(gmv) as total_gmv
FROM daily_metrics
WHERE site = 'DE'
  AND category = 'Electronics'
  AND date >= CURRENT_DATE - INTERVAL 7 DAY
GROUP BY date
ORDER BY date;
```

**Key Features:**
- Schema awareness（了解表结构）
- Error recovery（SQL 错误自动修正）
- Query validation（防止危险查询）

---

#### **3. Diagnosis Agent**

**职责：** 根因分析

**Workflow:**

```python
async def diagnose_anomaly(metric, site, category, date):
    # Step 1: 获取历史数据
    historical = await fetch_historical(metric, site, category, 90)

    # Step 2: 检测异常
    anomaly_score = detect_anomaly(historical, date)

    # Step 3: 贡献度分解
    contributions = await contribution_analysis(metric, date)

    # Step 4: 假设生成
    hypotheses = generate_hypotheses(contributions)

    # Step 5: 证据收集
    evidence = await collect_evidence(hypotheses)

    # Step 6: 根因排序
    ranked_causes = rank_by_confidence(evidence)

    return {
        "anomaly_score": anomaly_score,
        "contributions": contributions,
        "root_causes": ranked_causes[:3],  # Top 3
        "confidence": calculate_confidence(evidence)
    }
```

**Hypothesis Types:**

1. **Traffic Drop**
   - Check: impressions, clicks trend
   - Evidence: CTR stable but impressions down 30%

2. **Conversion Issue**
   - Check: CVR, checkout abandonment
   - Evidence: CVR dropped from 3.2% to 2.1%

3. **Campaign Overlap**
   - Check: multiple campaigns in same period
   - Evidence: 3 campaigns running, cannibalization

4. **Seller Churn**
   - Check: active_sellers count
   - Evidence: Top 5 sellers went inactive

5. **Seasonality**
   - Check: YoY comparison
   - Evidence: Same pattern last year

---

#### **4. Chart Generation Agent**

**职责：** 自动选择合适的图表类型

```python
def select_chart_type(data, intent):
    if intent == "trend":
        return "line_chart"
    elif intent == "comparison":
        return "bar_chart" if len(data) < 10 else "table"
    elif intent == "distribution":
        return "histogram"
    elif intent == "correlation":
        return "scatter_plot"
    else:
        return "table"
```

**Output Format:**
```json
{
  "chart_type": "line_chart",
  "data": [...],
  "config": {
    "x_axis": "date",
    "y_axis": "gmv",
    "title": "GMV Trend - Last 30 Days",
    "annotations": [
      {"date": "2027-01-10", "label": "Campaign Started"}
    ]
  }
}
```

---

### 3.3 Tool Registry

```python
TOOLS = [
    {
        "name": "query_database",
        "description": "Execute SQL query on DuckDB",
        "parameters": {
            "sql": "string",
            "timeout": "integer (optional)"
        }
    },
    {
        "name": "detect_anomalies",
        "description": "Run anomaly detection algorithm",
        "parameters": {
            "metric": "string",
            "site": "string",
            "date_range": "array"
        }
    },
    {
        "name": "calculate_contribution",
        "description": "Decompose metric change by dimensions",
        "parameters": {
            "metric": "string",
            "dimensions": "array",
            "base_period": "string",
            "compare_period": "string"
        }
    },
    {
        "name": "generate_chart",
        "description": "Create visualization",
        "parameters": {
            "chart_type": "string",
            "data": "array",
            "config": "object"
        }
    },
    {
        "name": "search_campaigns",
        "description": "Find campaigns in date range",
        "parameters": {
            "site": "string",
            "date_range": "array"
        }
    }
]
```

---

## 4. API Design

### 4.1 Endpoint Structure

```
/api/v1
├── /dashboard
│   ├── GET /kpis              # Dashboard KPI cards
│   ├── GET /trends            # 30-day trend data
│   └── GET /anomalies         # Recent anomalies
│
├── /diagnosis
│   ├── POST /analyze          # Trigger diagnosis
│   └── GET /result/{id}       # Get diagnosis result
│
├── /chat
│   ├── POST /query            # Natural language query
│   └── POST /stream           # SSE streaming response
│
├── /report
│   ├── POST /generate         # Generate report
│   └── GET /export/{id}       # Download report
│
└── /data
    ├── GET /sites             # List of sites
    ├── GET /categories        # List of categories
    └── POST /query            # Direct SQL execution (admin)
```

---

### 4.2 Example API Call

#### **Request: Natural Language Query**

```http
POST /api/v1/chat/query
Content-Type: application/json

{
  "query": "为什么德国站 GMV 下降了?",
  "context": {
    "session_id": "abc123",
    "history": []
  }
}
```

#### **Response:**

```json
{
  "status": "success",
  "query_id": "q_789xyz",
  "response": {
    "text": "德国站 GMV 下降 15% 的主要原因是物流延迟导致转化率下降。",
    "data": {
      "gmv_change": -0.15,
      "root_causes": [
        {
          "cause": "conversion_drop",
          "confidence": 0.87,
          "evidence": "CVR 从 3.2% 降至 2.1%",
          "contribution": 0.65
        },
        {
          "cause": "logistics_delay",
          "confidence": 0.78,
          "evidence": "平均配送时间从 5 天增至 9 天",
          "contribution": 0.25
        }
      ]
    },
    "chart": {
      "type": "line",
      "data": [...]
    }
  },
  "execution_time_ms": 2340
}
```

---

### 4.3 SSE Streaming (Real-time AI Response)

```http
POST /api/v1/chat/stream
Content-Type: application/json

{
  "query": "分析德国站问题"
}
```

**Response (SSE):**

```
event: status
data: {"step": "understanding_query"}

event: status
data: {"step": "querying_database"}

event: data
data: {"partial_result": {"gmv_drop": -0.15}}

event: status
data: {"step": "diagnosing_root_cause"}

event: final
data: {"response": {...}}
```

---

## 5. Repository Structure

```
business-signal-pilot/
├── frontend/                    # Next.js frontend
│   ├── app/
│   │   ├── (dashboard)/
│   │   │   ├── page.tsx        # Dashboard page
│   │   │   └── components/
│   │   │       ├── KPICard.tsx
│   │   │       ├── TrendChart.tsx
│   │   │       └── AnomalyAlert.tsx
│   │   ├── diagnosis/
│   │   │   ├── page.tsx        # Diagnosis page
│   │   │   └── components/
│   │   │       ├── DiagnosisPanel.tsx
│   │   │       └── CauseTree.tsx
│   │   ├── chat/
│   │   │   ├── page.tsx        # Ask AI page
│   │   │   └── components/
│   │   │       ├── ChatInterface.tsx
│   │   │       └── MessageBubble.tsx
│   │   └── report/
│   │       ├── page.tsx        # Report page
│   │       └── components/
│   │           └── ReportGenerator.tsx
│   ├── components/ui/          # shadcn components
│   ├── lib/
│   │   ├── api.ts              # API client
│   │   └── utils.ts
│   ├── public/
│   ├── package.json
│   └── tailwind.config.ts
│
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app entry
│   │   ├── api/
│   │   │   ├── dashboard.py
│   │   │   ├── diagnosis.py
│   │   │   ├── chat.py
│   │   │   └── report.py
│   │   ├── agents/
│   │   │   ├── orchestrator.py
│   │   │   ├── sql_agent.py
│   │   │   ├── diagnosis_agent.py
│   │   │   └── chart_agent.py
│   │   ├── core/
│   │   │   ├── config.py       # Settings
│   │   │   ├── database.py     # DuckDB connection
│   │   │   └── llm.py          # Claude/OpenAI client
│   │   ├── models/
│   │   │   ├── schemas.py      # Pydantic models
│   │   │   └── database.py     # SQLAlchemy (optional)
│   │   └── utils/
│   │       ├── anomaly_detection.py
│   │       ├── contribution_analysis.py
│   │       └── query_builder.py
│   ├── tests/
│   ├── requirements.txt
│   └── pyproject.toml
│
├── data/
│   ├── generate_data.py        # Synthetic data generator
│   ├── signal.db               # DuckDB file (gitignored)
│   └── seed/
│       └── anomalies.json      # Pre-defined anomalies
│
├── docs/
│   ├── PRD.md                  # Product requirements
│   ├── ARCHITECTURE.md         # This file
│   ├── API.md                  # API documentation
│   └── DEPLOYMENT.md           # Deployment guide
│
├── scripts/
│   ├── setup.sh                # Initial setup
│   ├── dev.sh                  # Run dev servers
│   └── deploy.sh               # Deploy to production
│
├── .github/
│   └── workflows/
│       └── ci.yml              # CI/CD pipeline
│
├── .env.example
├── .gitignore
├── README.md
├── CLAUDE.md                   # Claude Code instructions
└── LICENSE
```

---

## 6. Deployment Architecture

### 6.1 Development

```
Developer Machine
├── Frontend: localhost:3000 (Next.js dev server)
└── Backend: localhost:8000 (FastAPI with uvicorn --reload)
```

### 6.2 Production

```
┌─────────────────────────────────────┐
│         Vercel (Frontend)           │
│  • Edge network CDN                 │
│  • Automatic HTTPS                  │
│  • Preview deployments              │
└──────────────┬──────────────────────┘
               │
               │ API proxy
               │
┌──────────────▼──────────────────────┐
│      Fly.io / Modal (Backend)       │
│  • Auto-scaling                     │
│  • Regional deployment              │
│  • Environment secrets              │
└──────────────┬──────────────────────┘
               │
               ├─────────┬─────────────┐
               │         │             │
        ┌──────▼────┐  ┌─▼────────┐  ┌▼──────────┐
        │  DuckDB   │  │ Claude   │  │ OpenAI    │
        │  Volume   │  │   API    │  │   API     │
        └───────────┘  └──────────┘  └───────────┘
```

---

## 7. Performance Considerations

### 7.1 Query Optimization

**Problem:** 100 万行数据查询可能很慢

**Solutions:**

1. **Pre-aggregation**
   ```sql
   CREATE TABLE daily_metrics_summary AS
   SELECT
     date, site,
     SUM(gmv) as total_gmv
   FROM daily_metrics
   GROUP BY date, site;
   ```

2. **Columnar Storage**
   - DuckDB 默认列式存储，扫描更快

3. **Result Caching**
   ```python
   from functools import lru_cache

   @lru_cache(maxsize=100)
   def get_dashboard_kpis(site, date_range):
       ...
   ```

4. **Parallel Processing**
   ```python
   import polars as pl

   df = pl.read_database(query)  # 比 pandas 快 5-10x
   ```

---

### 7.2 AI Response Time

**Target:** < 10 秒

**Optimizations:**

1. **Streaming Response**
   - 用户边看边等待，感知更快

2. **Prompt Caching** (Claude)
   - System prompt 缓存，节省 90% token

3. **Tool Parallelization**
   ```python
   results = await asyncio.gather(
       sql_agent.query(),
       chart_agent.generate(),
       diagnosis_agent.analyze()
   )
   ```

4. **Fallback to Simpler Model**
   - 简单查询用 Haiku (更快更便宜)
   - 复杂诊断用 Sonnet

---

## 8. Security & Privacy

### 8.1 Data Security

- ✅ 所有数据是合成的，无隐私问题
- ✅ 生产环境使用 HTTPS
- ✅ API keys 存储在环境变量
- ✅ DuckDB 文件读写权限限制

### 8.2 API Security

```python
from fastapi import Depends, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key")

async def verify_api_key(api_key: str = Depends(api_key_header)):
    if api_key != settings.API_KEY:
        raise HTTPException(status_code=403)
```

### 8.3 Rate Limiting

```python
from slowapi import Limiter

limiter = Limiter(key_func=lambda: "global")

@app.post("/api/v1/chat/query")
@limiter.limit("10/minute")  # 防止滥用
async def chat_query(request: QueryRequest):
    ...
```

---

## 9. Monitoring & Observability

### 9.1 Metrics to Track

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| API Response Time | < 2s | > 5s |
| AI Query Success Rate | > 95% | < 90% |
| Database Query Time | < 500ms | > 2s |
| Error Rate | < 1% | > 5% |

### 9.2 Logging Strategy

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "query_executed",
    query_id=query_id,
    user_query=query,
    execution_time=elapsed,
    result_count=len(results)
)
```

---

## 10. Testing Strategy

### 10.1 Test Pyramid

```
       ┌─────┐
       │  E2E │  (10%)  Playwright
       └─────┘
      ┌───────┐
      │ Integr│  (30%)  FastAPI TestClient
      └───────┘
    ┌──────────┐
    │   Unit   │  (60%)  Pytest
    └──────────┘
```

### 10.2 Test Cases

**Critical Paths:**

1. ✅ Dashboard loads in < 2s
2. ✅ AI correctly answers "Why did GMV drop?"
3. ✅ Diagnosis identifies correct root cause
4. ✅ Report generates without errors
5. ✅ SQL injection prevented

---

## 11. Future Enhancements

### Phase 2 (Post-MVP)

1. **Real-time Streaming**
   - Replace DuckDB with ClickHouse
   - Apache Kafka for event ingestion

2. **Advanced AI**
   - Fine-tuned model for business analytics
   - Multi-modal analysis (include images)

3. **Collaboration**
   - Share diagnoses with team
   - Comment on anomalies
   - Permission management

4. **Mobile App**
   - React Native
   - Push notifications for alerts

---

## Appendix

### A. Tech Choices Rationale

**Why DuckDB over PostgreSQL?**
- ✅ 嵌入式，无需部署
- ✅ OLAP 优化，聚合查询更快
- ✅ 可以直接读 Parquet 文件

**Why FastAPI over Flask?**
- ✅ 异步原生支持
- ✅ 自动生成 OpenAPI 文档
- ✅ Pydantic 数据验证

**Why Polars over Pandas?**
- ✅ 性能快 5-10x
- ✅ 更好的类型系统
- ✅ 惰性求值优化

**Why Claude over OpenAI?**
- ✅ Function calling 更稳定
- ✅ 100k+ context window
- ✅ Prompt caching 省钱

---

### B. Performance Benchmarks (Target)

| Operation | Target | Actual (to measure) |
|-----------|--------|---------------------|
| Dashboard initial load | < 2s | TBD |
| SQL query (1M rows) | < 500ms | TBD |
| AI diagnosis | < 10s | TBD |
| Report generation | < 30s | TBD |

---

### C. Cost Estimation

**Monthly Cost (1000 queries/day):**

| Service | Cost |
|---------|------|
| Vercel (Frontend) | $0 (Free tier) |
| Fly.io (Backend) | $5 (Hobby) |
| Claude API | ~$50 (30k queries × $0.0015) |
| Total | ~$55/month |

**Extremely affordable for a demo project.**

---

**Next Steps:**

1. ✅ PRD approved
2. ✅ Architecture designed
3. ⏭️ Generate synthetic data
4. ⏭️ Build backend API
5. ⏭️ Build frontend UI

---

*Last updated: 2027-01-15*
