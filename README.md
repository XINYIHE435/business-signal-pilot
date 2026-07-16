# SignalPilot

> AI-Powered Cross-border Business Signal Diagnosis Platform
>
> 将业务异常诊断时间从数小时缩短到数分钟

[![Next.js](https://img.shields.io/badge/Next.js-15-black)](https://nextjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688)](https://fastapi.tiangolo.com/)
[![Claude](https://img.shields.io/badge/Claude-Sonnet%204.5-orange)](https://www.anthropic.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-blue)](https://www.python.org/)
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

## ✨ 核心功能（已实现）

### 1️⃣ Dashboard - 业务监控驾驶舱 ✅

- 📊 **实时 KPI 监控**：GMV、Sold Items、CTR、CVR、ASP 五大核心指标
- 📈 **多指标趋势分析**：GMV、ASP、STR 三条趋势线并排展示
- 🔍 **多维度筛选**：
  - 站点筛选（10 个站点：US, DE, UK, AU, FR, IT, ES, CA, CN, JP）
  - 两级分类筛选（L1 一级分类 + L2 二级分类级联）
  - 灵活时间范围（7天/14天/30天/季度/年度）
- 🚨 **AI 自动异常检测**：环比变化超过阈值自动告警
- 📅 **Business Date 自动适配**：基于数据库最大日期计算，无需手动调整

**技术亮点**:
- V2 Schema 支持两级分类体系（L1: Electronics, L2: Phones）
- 所有时间计算基于数据库 Business Date，确保查询结果完整
- 响应式布局，趋势图横向 3 列并排

### 2️⃣ AI Chat - 自然语言查询 ✅

- 💬 **对话式数据分析**：用自然语言提问，AI 自动生成并执行 SQL
- 🤖 **智能意图识别**：自动识别查询、诊断、报告等意图
- 🎯 **SQL 自动生成**：基于 Business Date 生成正确的日期过滤条件
- 📊 **结构化数据展示**：表格形式展示查询结果

**示例问题：**
- "美国站过去 7 天的 GMV 是多少？"
- "按 L2 分类汇总 GMV"
- "库存健康度分析"
- "德国站 Electronics 分类的 ASP 趋势"

**技术亮点**:
- LangGraph 多 Agent 编排（Orchestrator + SQL Agent）
- Claude Sonnet 4.5 驱动
- Schema 上下文自动注入 Business Date
- 禁止使用 `CURRENT_DATE`，使用显式日期字面量

### 🚧 规划中的功能

- **Diagnosis Agent**：自动根因分析 + 贡献度拆解
- **Report Generation**：一键生成周报/月报
- **高级可视化**：交互式图表、下钻分析
- **多轮对话上下文**：记忆历史对话内容

---

## 🛠️ 技术栈

### Frontend
- **Framework:** Next.js 15.1 (App Router)
- **Language:** TypeScript
- **UI:** Tailwind CSS + Custom Components
- **Charts:** Recharts
- **Data Fetching:** SWR
- **Icons:** Lucide React

### Backend
- **Framework:** FastAPI 0.138
- **Language:** Python 3.11+
- **Database:** DuckDB 1.1.3 (嵌入式 OLAP)
- **AI:** Claude Sonnet 4.5 (Anthropic)
- **Orchestration:** LangGraph
- **Logging:** Structlog

### Data
- **Storage:** DuckDB (列式存储，OLAP 优化)
- **Schema:** V2 两级分类体系
- **Data Range:** 2024-01-01 ~ 2026-07-12 (924 天)
- **Volume:** 
  - daily_metrics: 593,808 行
  - seller_daily_metrics: 4,156,656 行
  - inventory_daily: 593,808 行
  - campaigns: 47 行
  - sellers: 1,000 行

---

## 🚀 Quick Start

### 前置要求

- **Python 3.11+**
- **Node.js 18+**
- **pnpm** (推荐) 或 npm

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/business-signal-pilot.git
cd business-signal-pilot
```

### 2. 配置环境变量

```bash
# Backend
cd backend
cp .env.example .env
# 编辑 .env，填入 Anthropic API Key
echo "ANTHROPIC_API_KEY=your_api_key_here" >> .env
echo "ANTHROPIC_BASE_URL=https://api.anthropic.com" >> .env

# Frontend
cd ../frontend
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

### 3. 安装依赖

```bash
# Backend
cd backend
pip install -r requirements.txt

# 或手动安装核心依赖
pip install fastapi==0.138.0 uvicorn==0.49.0 structlog==26.1.0 \
    anthropic pydantic-settings duckdb langgraph langchain-anthropic
```

```bash
# Frontend
cd frontend
pnpm install

# 或使用 npm
npm install
```

### 4. 验证数据库

数据库文件已包含在项目中：

```bash
# 检查数据库
ls -lh data/signal.db

# 验证数据
python -c "
import duckdb
conn = duckdb.connect('data/signal.db')
print('daily_metrics:', conn.execute('SELECT COUNT(*) FROM daily_metrics').fetchone()[0], 'rows')
print('Business Date:', conn.execute('SELECT MAX(date) FROM daily_metrics').fetchone()[0])
conn.close()
"
```

如果需要重新生成数据：

```bash
cd data
python generate_data_v2.py
```

### 5. 启动服务

**Terminal 1 - Backend:**
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
pnpm dev
```

### 6. 访问应用

- **Frontend Dashboard**: http://localhost:3000
- **AI Chat**: http://localhost:3000/chat
- **Backend API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Business Date**: http://localhost:8000/api/v1/dashboard/business-date

---

## 📁 项目结构

```
business-signal-pilot/
├── backend/                 # FastAPI 后端
│   ├── app/
│   │   ├── main.py         # 应用入口
│   │   ├── api/
│   │   │   ├── dashboard_v2.py  # Dashboard API (V2 Schema)
│   │   │   └── chat.py          # Chat API
│   │   ├── agents/
│   │   │   ├── orchestrator_v2.py  # 主编排器
│   │   │   ├── sql_agent.py        # SQL 生成 Agent
│   │   │   └── intent_classifier.py
│   │   ├── core/
│   │   │   ├── database_v2.py   # 数据库连接 (V2)
│   │   │   ├── config.py        # 配置管理
│   │   │   └── llm.py           # LLM 客户端
│   │   └── models/
│   │       └── schemas.py       # Pydantic 模型
│   └── tests/              # 测试
├── frontend/               # Next.js 前端
│   ├── app/
│   │   ├── page.tsx       # Dashboard 主页
│   │   └── chat/
│   │       └── page.tsx   # AI Chat 页面
│   ├── components/
│   │   ├── KPICard.tsx           # KPI 卡片
│   │   ├── MultiTrendChart.tsx   # 多指标趋势图
│   │   ├── CategoryFilter.tsx    # 两级分类筛选器
│   │   └── AnomalyAlert.tsx      # 异常告警
│   └── lib/
│       └── api.ts         # API 客户端
├── data/
│   ├── generate_data_v2.py  # V2 数据生成器
│   ├── validate_data_v2.py  # 数据验证脚本
│   └── signal.db            # DuckDB 数据库 (593K+ 行)
├── docs/                 # 项目文档
│   ├── PRD.md           # 产品需求文档
│   ├── ARCHITECTURE.md  # 技术架构
│   └── archive/         # 历史文档归档
├── CLAUDE.md            # Claude AI 开发指南
├── README.md            # 项目说明（本文件）
├── QUICKSTART.md        # 快速启动指南
└── STATUS.md            # 项目状态追踪
```

---

## 🎯 核心技术亮点

### 1. Business Date 自动适配 ⭐

**问题**: 静态数据库（2024-01-01 ~ 2026-07-12）vs 系统时间不一致，导致查询结果为空

**解决方案**:
- 所有 API 端点使用 `database_v2.get_max_date()` 获取 Business Date
- SQL Agent 在 Schema 中注入 Business Date 上下文
- 禁止使用 `CURRENT_DATE`，强制使用显式日期字面量

**效果**:
- ✅ 查询"过去 7 天"永远返回完整数据
- ✅ 数据更新后自动适配，零维护
- ✅ Dashboard 和 SQL Agent 时间语义统一

### 2. V2 Schema 两级分类体系 ⭐

**特性**:
- L1 一级分类：20 个（Electronics, Fashion, Home...）
- L2 二级分类：81 个（Phones, Laptops, Cameras...）
- 级联筛选：先选 L1，再选 L2
- 向后兼容：Dashboard API 支持 V1/V2 Schema 自动适配

**数据结构**:
```sql
daily_metrics (
  date, site,
  category_l1, category_l2,      -- 分类名称
  category_id_l1, category_id_l2, -- 分类 ID
  gmv, sold_items, asp, str, ...
  PRIMARY KEY (date, site, category_id_l1, category_id_l2)
)
```

### 3. LangGraph 多 Agent 编排 ⭐

**架构**:
```
User Query
    ↓
Intent Classifier → 识别意图（query/diagnosis/report）
    ↓
Orchestrator V2 → 路由到对应 Agent
    ↓
SQL Agent → 生成 SQL + 执行查询 → 返回结果
```

**优势**:
- 清晰的职责分离
- 可扩展（新增 Agent 不影响现有逻辑）
- 可追踪（完整的 reasoning trace）

### 4. 性能优化 ⭐

- **DuckDB 列式存储**：OLAP 优化，聚合查询速度快
- **批量插入**：50K 行/批，避免内存溢出
- **索引优化**：date, site, category_id_l1, category_id_l2 复合主键
- **前端缓存**：SWR 自动缓存，减少重复请求

---

## 📊 数据概览

### 业务维度
- **站点数**: 10 个（US, DE, UK, AU, FR, IT, ES, CA, CN, JP）
- **L1 分类**: 20 个
- **L2 分类**: 81 个
- **时间范围**: 2024-01-01 ~ 2026-07-12 (924 天)

### 数据规模
| 表名 | 行数 | 说明 |
|------|------|------|
| daily_metrics | 593,808 | 站点 × 分类 × 日期 |
| seller_daily_metrics | 4,156,656 | 卖家级别明细 |
| inventory_daily | 593,808 | 库存健康度 |
| campaigns | 47 | 营销活动 |
| sellers | 1,000 | 卖家信息 |

### 数据质量
- ✅ **GMV 精度**: 平均误差 0.0048%（可接受的舍入误差）
- ✅ **Top-down 一致性**: Seller GMV 汇总 = Daily GMV（100% 匹配）
- ✅ **日期完整性**: 无缺失日期
- ✅ **维度完整性**: 所有站点 × 分类组合都有数据

---

## 🧪 测试

### 功能测试

```bash
# 1. 测试 Business Date
curl http://localhost:8000/api/v1/dashboard/business-date
# 预期: {"business_date": "2026-07-12", ...}

# 2. 测试 Dashboard KPI
curl "http://localhost:8000/api/v1/dashboard/kpis?site=US&days=7"
# 预期: date_range 为 "2026-07-05 to 2026-07-12"

# 3. 测试 SQL Agent
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "美国站过去 7 天的 GMV"}'
# 预期: SQL 包含 date >= '2026-07-05' AND date <= '2026-07-12'
```

### 单元测试

```bash
# Backend 测试
cd backend
pytest tests/

# Frontend 类型检查
cd frontend
pnpm tsc --noEmit
```

---

## 📚 核心文档

### 产品文档
- [📋 PRD - 产品需求文档](docs/PRD.md) - 业务背景、核心功能、技术方案
- [🏗️ ARCHITECTURE - 技术架构](docs/ARCHITECTURE.md) - 系统架构、数据流、技术选型

### 开发文档
- [📅 DEVELOPMENT_PLAN - 开发计划](docs/DEVELOPMENT_PLAN.md) - 里程碑、任务分解
- [💻 VIBE_CODING - 开发指南](docs/VIBE_CODING.md) - 编码规范、最佳实践
- [🤖 CLAUDE.md - AI 开发指南](CLAUDE.md) - Claude Code 项目配置

### 状态追踪
- [✅ STATUS.md - 项目状态](STATUS.md) - 当前进度、已完成功能、待办事项
- [🚀 QUICKSTART.md - 快速启动](QUICKSTART.md) - 详细的安装和配置指南

### 技术文档
- [📘 BUSINESS_DATE_REFACTOR.md](docs/archive/BUSINESS_DATE_REFACTOR.md) - Business Date 重构说明
- [📗 SQL_AGENT_BUSINESS_DATE_FIX.md](SQL_AGENT_BUSINESS_DATE_FIX.md) - SQL Agent 时间逻辑修复
- [📕 PHASE3_PREPARATION_COMPLETE.md](PHASE3_PREPARATION_COMPLETE.md) - Phase 3 准备工作总结

---

## 🎓 学习价值

这个项目展示了：

### 产品能力
- ✅ 从真实业务痛点出发（基于 eBay 实习经验）
- ✅ MVP 功能范围设计（先 Dashboard，再 AI Chat）
- ✅ 用户体验打磨（响应式布局、友好的错误提示）

### 技术能力
- ✅ **AI Agent 架构**：LangGraph 多 Agent 编排
- ✅ **全栈开发**：Next.js + FastAPI + DuckDB
- ✅ **数据工程**：V2 Schema 设计、批量数据生成
- ✅ **API 设计**：RESTful API + OpenAPI 文档

### 工程能力
- ✅ **代码组织清晰**：模块化、职责分离
- ✅ **完整的文档**：PRD、架构、开发指南、API 文档
- ✅ **可部署可演示**：Docker 支持、详细的部署指南
- ✅ **Business Date 设计**：自动适配数据范围，零维护

---

## 🚧 当前开发状态

### ✅ 已完成（Phase 1-2）
- [x] Dashboard V2（支持两级分类、多指标趋势图）
- [x] AI Chat（自然语言查询、SQL 自动生成）
- [x] Business Date 自动适配
- [x] V2 Schema 数据生成（593K+ 行）
- [x] LangGraph Agent 编排
- [x] API 文档（Swagger）

### 🚧 进行中（Phase 3）
- [ ] Diagnosis Agent（根因分析）
- [ ] Report Generation（周报/月报生成）
- [ ] 高级可视化（交互式图表）
- [ ] 多轮对话上下文

### 📋 待规划（Phase 4+）
- [ ] 实时数据接入
- [ ] 用户权限管理
- [ ] 多租户支持
- [ ] 移动端适配

详见 [STATUS.md](STATUS.md) 和 [docs/DEVELOPMENT_PLAN.md](docs/DEVELOPMENT_PLAN.md)

---

## 🤝 贡献

欢迎提 Issue 和 PR！

**如何贡献**:
1. Fork 本仓库
2. 创建 feature 分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

**代码规范**:
- Backend: PEP 8 (使用 `black` 格式化)
- Frontend: ESLint + Prettier
- Commit Message: 遵循 Conventional Commits

---

## 📄 License

[MIT](LICENSE)

---

## 🙏 致谢

- [Anthropic](https://www.anthropic.com/) - Claude API
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python Web Framework
- [Next.js](https://nextjs.org/) - The React Framework
- [DuckDB](https://duckdb.org/) - In-Process OLAP Database
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent Orchestration
- eBay China Analytics Team - 灵感来源

---

**Built with ❤️ by [Your Name]**

如果这个项目对你有帮助，请给个 ⭐️ Star！
