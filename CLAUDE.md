# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**SignalPilot** - AI 驱动的跨境商业信号诊断平台

这是一个模拟 eBay 内部分析工具的 AI 产品项目，用于 2027 年校招作品集展示。

**核心价值:** 将业务异常诊断时间从数小时缩短到数分钟。

**主要功能:**
1. **Dashboard** - 业务监控、KPI 展示、异常检测
2. **Diagnosis** - AI 自动根因分析、贡献度拆解
3. **Ask AI** - 自然语言查询业务数据
4. **Report** - 一键生成周报/月报

## 技术栈

- **Frontend:** Next.js 14 (App Router) + Tailwind + shadcn/ui + Plotly
- **Backend:** FastAPI + Python 3.11+ + Pydantic
- **Database:** DuckDB (嵌入式 OLAP，无需部署)
- **Data Processing:** Polars (比 Pandas 快 5-10x)
- **AI:** Claude 3.5 Sonnet / OpenAI GPT-4
- **Deploy:** Vercel (Frontend) + Fly.io (Backend)

## 项目结构

```
business-signal-pilot/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── main.py      # FastAPI app 入口
│   │   ├── api/         # API routes (dashboard, diagnosis, chat, report)
│   │   ├── agents/      # AI agents (orchestrator, sql_agent, diagnosis_agent)
│   │   ├── core/        # 核心工具 (config, database, llm)
│   │   ├── models/      # Pydantic schemas
│   │   └── utils/       # 工具函数 (anomaly_detection, contribution_analysis)
│   └── tests/
├── frontend/            # Next.js 前端
│   ├── app/
│   │   ├── (dashboard)/ # Dashboard 页面
│   │   ├── diagnosis/   # 诊断页面
│   │   ├── chat/        # Ask AI 页面
│   │   └── report/      # 报告页面
│   ├── components/      # React 组件
│   └── lib/            # API client
├── data/
│   ├── generate_data.py # 合成数据生成器
│   └── signal.db       # DuckDB 数据库文件 (gitignored)
├── docs/
│   ├── PRD.md          # 产品需求文档
│   ├── ARCHITECTURE.md # 技术架构
│   ├── DEVELOPMENT_PLAN.md # 开发计划
│   └── VIBE_CODING.md  # 开发执行指南
└── scripts/
    ├── setup.sh        # 初始化脚本
    └── dev.sh          # 开发启动脚本
```

## 常用命令

### 开发环境启动

```bash
# Backend (Terminal 1)
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
uvicorn app.main:app --reload

# Frontend (Terminal 2)
cd frontend
pnpm dev
```

### 数据生成

```bash
python data/generate_data.py
```

### 测试

```bash
# Backend 测试
cd backend
pytest

# Frontend 类型检查
cd frontend
pnpm tsc --noEmit

# Lint
cd frontend
pnpm lint
```

### 构建

```bash
# Backend
cd backend
python -m app.main

# Frontend
cd frontend
pnpm build
pnpm start
```

## 开发原则

### 代码风格

**通用规则:**
- 使用简体中文编写所有注释和文档
- 代码简洁，避免过度抽象
- 优先使用函数式编程，避免 class（除非必要）

**TypeScript:**
- 使用 ESM: `import { xxx } from 'xxx'`
- 优先命名导入而非默认导入
- 使用 `const` 而不是 `let`
- Server Components 优先，Client Components 显式标记 `'use client'`
- 优先使用 shadcn/ui 组件

**Python:**
- 使用 type hints
- 遵循 PEP 8
- 使用 `async/await` 进行异步操作
- Docstring 使用 Google 风格
- 函数命名使用 snake_case

### 架构模式

**AI Agent 设计:**
- Orchestrator 负责调度其他 Agent
- 每个 Agent 单一职责（SQL 生成、诊断、图表生成）
- 使用 Function Calling 而非 Prompt Engineering
- 保留对话上下文（支持多轮对话）

**API 设计:**
- RESTful 风格
- 使用 Pydantic 进行数据验证
- 所有错误返回友好的错误信息
- 长时间任务考虑使用 SSE streaming

**数据查询:**
- 优先使用 Polars 而不是 Pandas（性能更好）
- 复杂查询使用预聚合表
- 使用 `@lru_cache` 缓存查询结果
- 防止 SQL injection

### 依赖管理

- **包管理器:** 优先使用 pnpm，如使用 bun 需添加 `--no-cache` 参数
- **选择依赖:** 优先考虑流行度高、活跃维护、更新频繁的库
- **安装前搜索最佳实践**，避免使用过时或低质量的信息源（CSDN、云服务商社区等内容农场）

### 代码质量

- TypeScript 代码需通过 linter 检查
- 任务完成后运行 linter/formatter 自动化检查
- 添加适当的错误处理和 Loading 状态
- 使用 TypeScript 严格模式

## 开发工作流

### 添加新 API 端点

1. 在 `backend/app/models/schemas.py` 定义 Pydantic model
2. 在 `backend/app/api/` 创建对应的 route 文件
3. 在 `backend/app/main.py` 注册 router
4. 在 `backend/tests/` 添加测试
5. 更新 `frontend/lib/api.ts` 添加前端调用

### 添加新页面

1. 在 `frontend/app/` 创建新路由文件夹
2. 创建 `page.tsx` 和相关组件
3. 更新导航栏（如果需要）
4. 在 `lib/api.ts` 添加 API 调用

### 添加新 AI Agent

1. 在 `backend/app/agents/` 创建新 agent 文件
2. 定义 agent 的输入输出格式
3. 在 orchestrator 中注册新 agent
4. 添加单元测试验证功能

## 性能优化建议

- **Database:** 为常用查询字段创建索引
- **API:** 使用 Redis/内存缓存热点数据
- **Frontend:** 使用 `next/dynamic` 动态导入大组件，图表使用 `ssr: false`
- **AI:** 使用 Claude Prompt Caching，缓存 system prompt

## 调试技巧

### Backend 调试

```bash
# 启用详细日志
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload --log-level debug

# 查看生成的 SQL
# 在 sql_agent.py 中添加 logger.info("generated_sql", sql=sql)
```

### Frontend 调试

```typescript
// 在浏览器 console
localStorage.debug = '*'  // 查看所有 debug 日志
```

### 常见问题

1. **DuckDB 文件锁定** - 确保只有一个进程在写入
2. **CORS 错误** - 检查 FastAPI CORS 配置
3. **Claude API 超时** - 设置合理的 timeout (30-60s)
4. **类型错误** - 运行 `tsc --noEmit` 和 `mypy` 检查

## 重要文档

开始开发前，建议阅读：

1. **docs/PRD.md** - 理解产品目标和功能范围
2. **docs/ARCHITECTURE.md** - 了解系统架构和数据流
3. **docs/DEVELOPMENT_PLAN.md** - 查看 3 周开发计划
4. **docs/VIBE_CODING.md** - 具体的实现步骤和代码示例

## AI Agent 注意事项

当实现 AI 功能时：

- **SQL 生成** - 必须防止 SQL injection，验证生成的 SQL
- **诊断报告** - 提供数据源引用，显示推理过程
- **对话上下文** - 保留最近 5 轮对话，避免 token 浪费
- **错误处理** - LLM 可能返回非预期格式，需要 fallback 机制

## 数据说明

- 所有数据都是合成的，无真实用户信息
- `daily_metrics` 表包含约 220k 行数据（730 天 × 10 站点 × 30 品类）
- 数据中注入了 5% 的异常（流量下降、转化率下降、促销冲突等）
- 使用 `data/generate_data.py` 重新生成数据

## Demo 准备

项目完成后，准备 5 分钟 Demo:

1. **Dashboard** - 展示 KPI 监控和异常检测
2. **Diagnosis** - 点击异常，展示 AI 自动诊断过程
3. **Ask AI** - 演示自然语言查询："为什么德国站 GMV 下降？"
4. **Report** - 展示一键生成周报功能

**关键信息:**
- 强调 AI 自动化（从 4 小时降至 15 分钟）
- 展示技术深度（Agent workflow、数据处理）
- 说明产品思维（解决真实痛点）
