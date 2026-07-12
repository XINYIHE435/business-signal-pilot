# SignalPilot 企业级 AI Agent 架构设计

**版本:** 2.0  
**日期:** 2026-07-09  
**状态:** Architecture Design  
**作者:** Principal AI Architect  
**目标:** 从 MVP 升级为企业级 AI Business Analytics Agent 平台

---

## 执行摘要

SignalPilot 2.0 将从简单的 Dashboard + API 架构升级为真正的企业级 Multi-Agent 系统，参考 Microsoft Fabric Copilot、Salesforce Agentforce、Palantir AIP 的设计理念。

### 核心升级

- **LangGraph Multi-Agent 编排** - StateGraph 驱动的 Agent workflow
- **Tool Calling 架构** - 所有逻辑通过 Tool 暴露，不硬编码
- **MCP 集成接口** - 面向未来的企业系统对接标准
- **RAG 驱动检索** - Schema/Metrics/Policies 知识库
- **Database Abstraction** - 支持 DuckDB/PostgreSQL/Snowflake
- **Agent Observability** - 完整的推理轨迹和中间状态
- **Streaming Execution** - SSE 实时反馈
- **Long-term Memory** - 会话持久化和上下文管理

### 不是 ChatGPT Wrapper

- ❌ 不是简单的 Prompt Engineering
- ❌ 不是单一 LLM 调用
- ❌ 不是硬编码的 if-else 逻辑
- ✅ 是可编排的 Agent Workflow
- ✅ 是工具驱动的系统集成
- ✅ 是可扩展的企业架构

---

## 1. 架构对比

### 1.1 技术栈升级

| 组件 | 当前 (MVP) | 升级后 (Enterprise) | 原因 |
|------|-----------|-------------------|------|
| **编排引擎** | 无 | **LangGraph StateGraph** | 复杂 Agent 编排 |
| **Agent 框架** | 无 | **Multi-Agent System** | 模块化、可扩展 |
| **工具调用** | 硬编码逻辑 | **Tool Registry + Function Calling** | 动态、可配置 |
| **数据库访问** | 直接 DuckDB | **Database Abstraction Layer** | 支持多数据库 |
| **外部集成** | 无 | **MCP Client Interface** | 标准化集成 |
| **知识检索** | 无 | **RAG (ChromaDB)** | Schema/知识增强 |
| **可观测性** | 基础日志 | **Reasoning Traces** | 调试和审计 |
| **流式输出** | 无 | **SSE Streaming** | 实时反馈 |

### 1.2 数据流对比

**Before (MVP):**
```
User Query 
  → FastAPI Endpoint 
  → Hardcoded SQL 
  → DuckDB 
  → JSON Response
```

**After (Enterprise):**
```
User Query 
  → LangGraph Orchestrator
    ├─ Intent Classifier (LLM + Tool Calling)
    ├─ Planner (生成执行计划)
    ├─ Tool Executor
    │   ├─ SQL Tool (RAG + Database Abstraction)
    │   ├─ Campaign Tool (MCP Client)
    │   ├─ Policy Tool (RAG Retrieval)
    │   └─ Forecast Tool (Statistical)
    └─ Synthesizer (结果聚合)
  → SSE Streaming Response
```

### 1.3 系统架构图

```
┌────────────────────────────────────────────────────────────────┐
│                    Frontend (Next.js)                           │
│         Dashboard | Diagnosis | Ask AI | Report                │
└──────────────────────┬─────────────────────────────────────────┘
                       │ REST API / SSE
┌──────────────────────▼─────────────────────────────────────────┐
│                   FastAPI Gateway                               │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │           LangGraph Orchestration Engine                  │  │
│  │                                                          │  │
│  │   ┌──────────┐  ┌──────────┐  ┌──────────┐            │  │
│  │   │ Intent   │→ │ Planner  │→ │ Executor │            │  │
│  │   │Classifier│  │          │  │          │            │  │
│  │   └──────────┘  └──────────┘  └──────────┘            │  │
│  │                                                          │  │
│  └──────────────────────┬───────────────────────────────────┘  │
└─────────────────────────┼──────────────────────────────────────┘
                          │
┌─────────────────────────▼──────────────────────────────────────┐
│                    Specialized Agents                           │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐         │
│  │   SQL    │ │Diagnosis │ │  Report  │ │   Viz    │         │
│  │  Agent   │ │  Agent   │ │  Agent   │ │  Agent   │         │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘         │
└───────┼────────────┼────────────┼────────────┼────────────────┘
        │            │            │            │
┌───────▼────────────▼────────────▼────────────▼────────────────┐
│                       Tool Registry                             │
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐            │
│  │Database │ │Campaign │ │ Policy  │ │Forecast │            │
│  │  Tool   │ │Tool(MCP)│ │Tool(RAG)│ │  Tool   │            │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘            │
└───────┼───────────┼───────────┼───────────┼─────────────────┘
        │           │           │           │
┌───────▼───────────▼───────────▼───────────▼─────────────────┐
│                  Infrastructure Layer                         │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ Database │ │   MCP    │ │ Vector   │ │ External │       │
│  │Abstraction│ │ Servers  │ │  Store   │ │   APIs   │       │
│  │          │ │          │ │          │ │          │       │
│  │• DuckDB  │ │•Salesforce│ │• ChromaDB│ │• Holiday │       │
│  │• Postgres│ │• ERP     │ │• Schemas │ │• News    │       │
│  │•Snowflake│ │• CRM     │ │• Metrics │ │• Weather │       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└───────────────────────────────────────────────────────────────┘
```

---

