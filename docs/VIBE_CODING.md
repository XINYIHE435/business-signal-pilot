# SignalPilot - Vibe Coding Execution Guide

**Target:** Claude Code / Cursor / 人工开发
**Purpose:** 将 PRD + Architecture + Dev Plan 转化为可执行的开发步骤

---

## Part 1: Cursor Rules

创建 `.cursorrules` 文件，让 Cursor 理解项目上下文。

```markdown
# SignalPilot - AI-Powered Business Diagnosis Platform

## Project Overview

SignalPilot 是一个 AI 原生的跨境电商业务诊断平台，模拟 eBay 内部分析工具。

**核心功能:**
- Dashboard: 业务监控 + 异常检测
- Diagnosis: AI 根因分析
- Ask AI: 自然语言查询
- Report: 自动生成周报

**技术栈:**
- Frontend: Next.js 14 (App Router) + Tailwind + shadcn/ui
- Backend: FastAPI + Python 3.11+
- Database: DuckDB (嵌入式 OLAP)
- Data: Polars (高性能数据处理)
- AI: Claude 3.5 Sonnet / OpenAI GPT-4
- Visualization: Plotly.js

---

## Code Style

### General
- 使用简体中文编写注释和文档
- 优先使用函数式编程，避免 class
- 代码简洁，避免过度抽象
- 变量命名清晰（snake_case for Python, camelCase for TypeScript）

### TypeScript
- 使用 ESM (import/export)
- 优先命名导入: `import { foo } from 'bar'`
- 所有组件使用 TypeScript
- 使用 `const` 而不是 `let`，除非需要重新赋值
- 优先使用箭头函数

### Python
- 使用 type hints
- 遵循 PEP 8
- 使用 `async/await` 进行异步操作
- Docstring 使用 Google 风格

### React/Next.js
- 使用 Server Components (RSC) 优先
- Client components 显式标记 `'use client'`
- 优先使用 shadcn/ui 组件
- 避免不必要的 `useEffect`

---

## Common Tasks

### Task: Add a new API endpoint

1. 定义 Pydantic schema (`app/models/schemas.py`)
2. 创建 API route (`app/api/your_route.py`)
3. 在 `app/main.py` 中注册 router
4. 添加测试 (`tests/test_your_route.py`)

### Task: Add a new page

1. 创建 `app/your-page/page.tsx`
2. 创建相关组件 (`components/YourComponent.tsx`)
3. 添加到导航栏
4. 创建 API 调用函数 (`lib/api.ts`)

### Task: Add a new AI agent

1. 创建 `app/agents/your_agent.py`
2. 定义 tools (如果需要)
3. 在 orchestrator 中注册
4. 添加单元测试

---

## Quick Start Commands

### Setup
```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd frontend
pnpm install

# Generate data
python data/generate_data.py
```

### Development
```bash
# Terminal 1: Backend
cd backend
uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend
pnpm dev
```
```

保存为 `.cursorrules`

---

## Part 2: 项目初始化步骤

### Step 1: 创建项目结构

```bash
# 创建目录结构
mkdir -p backend/app/{api,agents,core,models,utils}
mkdir -p backend/tests
mkdir -p frontend
mkdir -p data/seed
mkdir -p scripts
mkdir -p docs

# 创建空文件
touch backend/app/__init__.py
touch backend/app/main.py
touch backend/requirements.txt
touch data/generate_data.py
touch scripts/setup.sh
touch scripts/dev.sh
```

### Step 2: Backend 初始化

**backend/requirements.txt**
```txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0
anthropic==0.18.0
openai==1.12.0
duckdb==0.10.0
polars==0.20.0
structlog==24.1.0
python-multipart==0.0.6
```

**backend/app/main.py**
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

# 配置日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

app = FastAPI(
    title="SignalPilot API",
    description="AI-Powered Business Diagnosis Platform",
    version="1.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "SignalPilot API", "status": "running"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**backend/app/core/config.py**
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # AI
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # Database
    database_path: str = "../data/signal.db"

    # API
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    cors_origins: str = "http://localhost:3000"

    # Logging
    log_level: str = "INFO"

    class Config:
        env_file = ".env"

settings = Settings()
```

**backend/app/core/database.py**
```python
import duckdb
from app.core.config import settings

class Database:
    """DuckDB 连接管理器"""

    def __init__(self):
        self.conn = None

    def connect(self):
        """建立数据库连接"""
        if self.conn is None:
            self.conn = duckdb.connect(settings.database_path, read_only=False)
        return self.conn

    def close(self):
        """关闭连接"""
        if self.conn:
            self.conn.close()
            self.conn = None

    def execute(self, query: str):
        """执行查询"""
        conn = self.connect()
        return conn.execute(query).fetchall()

db = Database()
```

### Step 3: Frontend 初始化

```bash
cd frontend
npx create-next-app@latest . --app --tailwind --typescript --no-src-dir
pnpm add @radix-ui/react-slot class-variance-authority clsx tailwind-merge lucide-react
pnpm add recharts plotly.js react-plotly.js
pnpm add swr
```

**frontend/lib/api.ts**
```typescript
const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export async function fetchAPI<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(`${API_URL}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  })

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`)
  }

  return response.json()
}

export const api = {
  dashboard: {
    getKPIs: () => fetchAPI('/api/v1/dashboard/kpis'),
    getTrends: () => fetchAPI('/api/v1/dashboard/trends'),
    getAnomalies: () => fetchAPI('/api/v1/dashboard/anomalies'),
  },
  chat: {
    query: (query: string) =>
      fetchAPI('/api/v1/chat/query', {
        method: 'POST',
        body: JSON.stringify({ query }),
      }),
  },
}
```

### Step 4: 生成合成数据

**data/generate_data.py**
```python
import duckdb
import random
from datetime import datetime, timedelta
import numpy as np

def generate_data():
    """生成合成业务数据"""

    conn = duckdb.connect('data/signal.db')

    # 创建 daily_metrics 表
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_metrics (
            date DATE NOT NULL,
            site VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            gmv DECIMAL(15, 2),
            sold_items INTEGER,
            impressions INTEGER,
            clicks INTEGER,
            orders INTEGER,
            ctr DECIMAL(5, 4),
            cvr DECIMAL(5, 4),
            asp DECIMAL(10, 2),
            active_sellers INTEGER,
            new_listings INTEGER,
            PRIMARY KEY (date, site, category)
        )
    """)

    sites = ['US', 'DE', 'UK', 'AU', 'FR', 'IT', 'ES', 'CA', 'CN', 'JP']
    categories = [
        'Electronics', 'Fashion', 'Home', 'Sports', 'Toys',
        'Books', 'Beauty', 'Automotive', 'Health', 'Garden',
        'Pet', 'Baby', 'Jewelry', 'Office', 'Music',
        'Video Games', 'Tools', 'Grocery', 'Handmade', 'Industrial',
        'Luggage', 'Shoes', 'Watches', 'Appliances', 'Furniture',
        'Arts', 'Crafts', 'Outdoor', 'Software', 'Collectibles'
    ]

    start_date = datetime(2025, 1, 1)
    end_date = datetime(2026, 12, 31)

    data = []
    current_date = start_date

    print(f"生成数据: {start_date} 到 {end_date}")

    while current_date <= end_date:
        for site in sites:
            for category in categories:
                # 基础指标
                base_gmv = random.uniform(50000, 500000)
                base_impressions = int(random.uniform(100000, 1000000))
                base_ctr = random.uniform(0.01, 0.05)
                base_cvr = random.uniform(0.02, 0.08)

                # 注入异常 (5% 概率)
                if random.random() < 0.05:
                    if random.random() < 0.3:  # 流量骤降
                        base_impressions = int(base_impressions * 0.5)
                    elif random.random() < 0.3:  # 转化率下降
                        base_cvr = base_cvr * 0.6
                    else:  # GMV 异常
                        base_gmv = base_gmv * 0.7

                clicks = int(base_impressions * base_ctr)
                orders = int(clicks * base_cvr)
                sold_items = int(orders * random.uniform(1.1, 1.5))
                asp = base_gmv / sold_items if sold_items > 0 else 0

                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'site': site,
                    'category': category,
                    'gmv': round(base_gmv, 2),
                    'sold_items': sold_items,
                    'impressions': base_impressions,
                    'clicks': clicks,
                    'orders': orders,
                    'ctr': round(base_ctr, 4),
                    'cvr': round(base_cvr, 4),
                    'asp': round(asp, 2),
                    'active_sellers': int(random.uniform(50, 500)),
                    'new_listings': int(random.uniform(100, 1000))
                })

        current_date += timedelta(days=1)

        if len(data) % 10000 == 0:
            print(f"已生成 {len(data)} 行...")

    # 批量插入
    print(f"插入 {len(data)} 行数据...")
    conn.executemany("""
        INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        d['date'], d['site'], d['category'], d['gmv'], d['sold_items'],
        d['impressions'], d['clicks'], d['orders'], d['ctr'], d['cvr'],
        d['asp'], d['active_sellers'], d['new_listings']
    ) for d in data])

    conn.execute("CREATE INDEX IF NOT EXISTS idx_date ON daily_metrics(date)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_site_category ON daily_metrics(site, category)")

    print(f"✅ 数据生成完成! 总行数: {len(data)}")

    # 验证
    result = conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()
    print(f"验证: {result[0]} 行")

    conn.close()

if __name__ == "__main__":
    generate_data()
```

### Step 5: 开发脚本

**scripts/setup.sh**
```bash
#!/bin/bash

echo "🚀 SignalPilot Setup"

# Backend
echo "📦 Setting up backend..."
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
echo "📦 Setting up frontend..."
cd ../frontend
pnpm install

# Generate data
echo "🗄️ Generating synthetic data..."
cd ..
python data/generate_data.py

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Copy .env.example to .env and fill in API keys"
echo "2. Run ./scripts/dev.sh to start development servers"
```

**scripts/dev.sh**
```bash
#!/bin/bash

echo "🚀 Starting SignalPilot development servers..."

# Start backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload --port 8000 &
BACKEND_PID=$!

# Start frontend
cd ../frontend
pnpm dev &
FRONTEND_PID=$!

echo "✅ Servers started!"
echo "Backend: http://localhost:8000"
echo "Frontend: http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop all servers"

# Wait for Ctrl+C
trap "kill $BACKEND_PID $FRONTEND_PID" EXIT
wait
```

---

## Part 3: Implementation Order

### Phase 1: Foundation (Day 1-2)

```bash
# 1. 初始化项目
./scripts/setup.sh

# 2. 生成数据
python data/generate_data.py

# 3. 测试 backend
cd backend
uvicorn app.main:app --reload
# 访问 http://localhost:8000/docs

# 4. 测试 frontend
cd frontend
pnpm dev
# 访问 http://localhost:3000
```

### Phase 2: Dashboard (Day 3-4)

**实现顺序:**

1. **Backend API**
   - `backend/app/api/dashboard.py`
   - 实现 `/api/v1/dashboard/kpis`
   - 实现 `/api/v1/dashboard/trends`

2. **Frontend Components**
   - `frontend/components/KPICard.tsx`
   - `frontend/components/TrendChart.tsx`
   - `frontend/app/(dashboard)/page.tsx`

3. **测试**
   - 访问 Dashboard
   - 验证 KPI 显示正确
   - 验证图表渲染

### Phase 3: AI Chat (Day 5-7)

**实现顺序:**

1. **SQL Agent**
   - `backend/app/agents/sql_agent.py`
   - 测试 SQL 生成

2. **Chat API**
   - `backend/app/api/chat.py`
   - 实现 `/api/v1/chat/query`

3. **Chat UI**
   - `frontend/app/chat/page.tsx`
   - `frontend/components/ChatInterface.tsx`

4. **测试**
   - 问 "德国站 GMV 如何?"
   - 验证返回正确答案

### Phase 4: Diagnosis (Week 2)

**实现顺序:**

1. **Anomaly Detection**
   - `backend/app/utils/anomaly_detection.py`

2. **Diagnosis Agent**
   - `backend/app/agents/diagnosis_agent.py`

3. **Diagnosis UI**
   - `frontend/app/diagnosis/page.tsx`

### Phase 5: Report (Week 2)

**实现顺序:**

1. **Report Generator**
   - `backend/app/utils/report_generator.py`

2. **Report API**
   - `backend/app/api/report.py`

3. **Report UI**
   - `frontend/app/report/page.tsx`

---

## Part 4: Testing Checklist

### Functionality Tests

- [ ] Dashboard 加载成功
- [ ] KPI 数字正确
- [ ] 趋势图渲染
- [ ] AI 回答 "德国站 GMV 如何?"
- [ ] AI 回答 "为什么下降?"
- [ ] Diagnosis 能诊断异常
- [ ] Report 生成成功
- [ ] 多轮对话工作正常

### Performance Tests

- [ ] Dashboard 加载 < 3s
- [ ] API 响应 < 1s
- [ ] AI 查询 < 10s
- [ ] Report 生成 < 30s

### Edge Cases

- [ ] 无数据时显示 Empty state
- [ ] API 错误时显示友好提示
- [ ] 网络超时处理
- [ ] SQL injection 防护

---

## Part 5: Demo Script (5 分钟)

```markdown
## Opening (30s)
"这是 SignalPilot，一个 AI 驱动的跨境电商业务诊断平台。
我在 eBay 实习时发现业务分析很依赖人工，所以做了这个项目。"

## Dashboard (1min)
"这是业务 Dashboard，实时监控 10 个站点、30 个品类的核心指标。
这里有个红色告警，AI 自动检测到 GMV 异常。"

## Diagnosis (2min)
"点击异常，AI Agent 自动启动诊断流程。
它会做贡献度分析、生成根因假设、收集证据。
在这个案例中，它发现是物流延迟导致转化率下降。"

## Ask AI (1.5min)
"我可以用自然语言提问：'为什么德国站 GMV 下降?'
AI 会生成 SQL、查询数据库、生成图表，全自动完成。
我还能追问：'如果补贴增加 10% 会怎样?'，它会做模拟分析。"

## Report (30s)
"最后，它能一键生成周报，包括 Executive Summary、Key Findings、建议动作。
以前需要 2 小时，现在 30 秒。"

## Closing (30s)
"技术栈是 Next.js + FastAPI + DuckDB + Claude API。
所有数据都是合成的，模拟真实 eBay 场景。
代码已开源，欢迎查看！"
```

---

## Part 6: 常见问题

### Q: DuckDB 文件很大怎么办?
A: 使用 Parquet 格式存储，压缩率更高。

### Q: Claude API 成本太高?
A: 使用 Prompt caching + 结果缓存，可降低 90% 成本。

### Q: 查询速度慢?
A: 创建预聚合表，使用 Polars 加速。

### Q: 如何部署?
A: Frontend 用 Vercel，Backend 用 Fly.io，DuckDB 挂载 Volume。

---

## Part 7: Next Steps

**完成 MVP 后:**

1. ✅ 部署到生产环境
2. ✅ 录制 Demo 视频
3. ✅ 完善文档
4. ✅ 添加到简历/作品集
5. ✅ 准备面试讲解

**可选优化:**

- 添加 What-if simulation
- 实现实时告警
- 支持多用户
- 移动端适配
- 国际化 (i18n)

---

**最重要的:**
专注核心价值，快速交付，展示你的产品思维和执行力！🚀
