# SignalPilot

> AI-Powered Cross-border Business Signal Diagnosis Platform
>
> 将业务异常诊断时间从数小时缩短到数分钟

[![Next.js](https://img.shields.io/badge/Next.js-14-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-009688)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/Claude-3.5%20Sonnet-orange)](https://www.anthropic.com/)
[![License](https://img.shields.io/badge/license-MIT-blue)](LICENSE)

---

## 📖 项目背景

这个项目的灵感来自于我在 **eBay 中国分析中心 (CBT Business Analytics)** 的实习经历。

在实习期间，我观察到业务分析的典型流程：

```
业务问题 → SQL 查询 → Tableau 可视化 → 手动分析 → PPT 报告
总耗时：4-8 小时
```

**核心痛点：**
- ⏱️ 异常发现滞后（3 天后才注意到）
- 🔍 根因分析依赖个人经验
- 📊 跨站点对比困难
- 📝 重复性报告工作占用大量时间

**SignalPilot 的解决方案：**

用 AI Agent 自动完成数据查询、异常检测、根因归因，让分析师专注于战略决策。

---

## ✨ 核心功能

### 1️⃣ Dashboard - 业务监控驾驶舱

- 📊 实时 KPI 监控（GMV、SI、CTR、CVR、ASP）
- 📈 30 天趋势可视化
- 🚨 AI 自动异常检测与告警
- 🔎 多维度筛选（站点、品类）

### 2️⃣ Diagnosis - AI 智能诊断

- 🤖 自动根因分析
- 📉 贡献度拆解（Site / Category / Seller）
- 💡 假设生成 + 证据收集
- ✅ 可执行的行动建议

### 3️⃣ Ask AI - 自然语言查询

- 💬 对话式数据分析
- 🔄 多轮上下文理解
- 📊 自动生成图表
- 🎯 SQL 自动生成 + 执行

**示例问题：**
- "为什么德国站 GMV 上周下降了 15%？"
- "哪些品类在 Black Friday 表现最好？"
- "如果补贴增加 10%，预计 GMV 增长多少？"

### 4️⃣ Report - 一键报告生成

- 📄 自动生成周报/月报
- ✍️ AI 撰写 Executive Summary
- 📋 Key Findings + Recommended Actions
- 💾 导出 Markdown / PDF

---

## 🛠️ 技术栈

### Frontend
- **Framework:** Next.js 14 (App Router)
- **UI:** Tailwind CSS + shadcn/ui
- **Charts:** Plotly.js
- **State:** SWR

### Backend
- **Framework:** FastAPI (Python 3.11+)
- **Database:** DuckDB (嵌入式 OLAP)
- **Data Processing:** Polars (比 Pandas 快 5-10x)
- **AI:** Claude 3.5 Sonnet / OpenAI GPT-4

### Infrastructure
- **Deploy:** Vercel (Frontend) + Fly.io (Backend)
- **CI/CD:** GitHub Actions

---

## 🚀 Quick Start

### 前置要求

- Python 3.11+
- Node.js 18+
- pnpm (推荐) 或 npm

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/business-signal-pilot.git
cd business-signal-pilot
```

### 2. 环境变量配置

```bash
# Backend
cd backend
cp .env.example .env
# 编辑 .env，填入你的 ANTHROPIC_API_KEY 或 OPENAI_API_KEY

# Frontend
cd ../frontend
cp .env.local.example .env.local
```

### 3. 安装依赖

```bash
# Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# Frontend
cd ../frontend
pnpm install
```

### 4. 生成合成数据

```bash
python data/generate_data.py
```

这会生成约 220k 行的业务数据（2 年历史数据）。

### 5. 启动开发服务器

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

### 6. 访问应用

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API 文档: http://localhost:8000/docs

---

## 📁 项目结构

```
business-signal-pilot/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── api/            # API 路由
│   │   ├── agents/         # AI Agents
│   │   ├── core/           # 核心配置
│   │   ├── models/         # 数据模型
│   │   └── utils/          # 工具函数
│   └── tests/              # 测试
├── frontend/               # Next.js 前端
│   ├── app/
│   │   ├── (dashboard)/    # Dashboard 页面
│   │   ├── diagnosis/      # 诊断页面
│   │   ├── chat/          # Ask AI 页面
│   │   └── report/        # 报告页面
│   ├── components/        # UI 组件
│   └── lib/              # 工具库
├── data/
│   ├── generate_data.py  # 数据生成器
│   └── signal.db         # DuckDB 数据库
├── docs/                 # 项目文档
│   ├── PRD.md           # 产品需求文档
│   ├── ARCHITECTURE.md  # 技术架构
│   ├── DEVELOPMENT_PLAN.md
│   └── VIBE_CODING.md
└── scripts/             # 自动化脚本
```

---

## 🎯 产品亮点

### 1. AI-Native 设计

不是简单的 ChatGPT 套壳，而是：
- 多 Agent 协作（Orchestrator + SQL Agent + Diagnosis Agent）
- Function Calling 精准调用工具
- 上下文感知的多轮对话

### 2. 真实业务场景

基于真实的 eBay 跨境电商分析场景：
- 10 个站点（US, DE, UK, AU...）
- 30 个品类（Electronics, Fashion, Home...）
- 5 种典型异常模式注入

### 3. 性能优化

- DuckDB 列式存储（OLAP 优化）
- Polars 数据处理（比 Pandas 快 5-10x）
- Claude Prompt Caching（节省 90% Token）
- SWR 数据缓存

### 4. 产品级体验

- 优雅的 Loading 状态
- 友好的错误提示
- Responsive 设计
- 完整的 API 文档

---

## 📊 Demo 展示

### Dashboard
![Dashboard](docs/images/dashboard.png)
*实时监控核心业务指标，自动检测异常*

### AI Diagnosis
![Diagnosis](docs/images/diagnosis.png)
*AI 自动诊断根因，提供可执行的建议*

### Ask AI
![Chat](docs/images/chat.png)
*自然语言查询，即问即答*

---

## 🧪 测试

```bash
# Backend 测试
cd backend
pytest

# Frontend 类型检查
cd frontend
pnpm tsc --noEmit

# Lint
pnpm lint
```

---

## 📦 部署

### Vercel (Frontend)

```bash
cd frontend
vercel --prod
```

### Fly.io (Backend)

```bash
cd backend
fly launch --name signalpilot-api
fly deploy
```

详细部署文档见 [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

---

## 📚 文档

- [📋 PRD - 产品需求文档](docs/PRD.md)
- [🏗️ ARCHITECTURE - 技术架构](docs/ARCHITECTURE.md)
- [📅 DEVELOPMENT_PLAN - 开发计划](docs/DEVELOPMENT_PLAN.md)
- [💻 VIBE_CODING - 开发指南](docs/VIBE_CODING.md)
- [🤖 CLAUDE - Claude Code 指令](CLAUDE.md)

---

## 🎓 学习价值

这个项目展示了：

### 产品能力
- ✅ 从真实业务痛点出发
- ✅ MVP 功能范围设计
- ✅ 用户体验打磨

### 技术能力
- ✅ AI Agent 架构设计
- ✅ 全栈开发（Next.js + FastAPI）
- ✅ 数据处理优化
- ✅ API 设计与文档

### 工程能力
- ✅ 代码组织清晰
- ✅ 完整的文档
- ✅ 可部署可演示

---

## 🤝 贡献

欢迎提 Issue 和 PR！

如果你觉得这个项目有帮助，请给个 ⭐️ Star

---

## 📄 License

[MIT](LICENSE)

---


---

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [Vercel](https://vercel.com/) - Frontend 部署
- [shadcn/ui](https://ui.shadcn.com/) - UI 组件库
- eBay China Analytics Team - 灵感来源

---
