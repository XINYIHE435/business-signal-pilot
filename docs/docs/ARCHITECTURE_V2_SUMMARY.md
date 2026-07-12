# SignalPilot 2.0 企业级架构概要

**版本:** 2.0  
**日期:** 2026-07-09  
**状态:** Implementation Starting  

---

## 核心升级

从简单的 Dashboard + API 升级为企业级 Multi-Agent 平台：

### 技术架构
- **LangGraph StateGraph** - Multi-Agent 编排引擎
- **Tool Registry** - 所有逻辑通过 Tool 暴露
- **Database Abstraction** - 支持多种数据库
- **MCP Client** - 标准化企业集成接口
- **RAG System** - Schema/Metrics/Policies 知识库
- **SSE Streaming** - 实时反馈
- **Reasoning Traces** - 完整可观测性

### Agent 体系
1. **Intent Classifier** - 理解用户意图
2. **SQL Agent** - Text-to-SQL (带 RAG)
3. **Diagnosis Agent** - 根因分析
4. **Report Agent** - 报告生成
5. **Viz Agent** - 图表配置
6. **Synthesizer** - 结果聚合

### Tool 体系
- **Database Tool** - SQL 执行 (带 Adapter)
- **Campaign Tool** - 促销查询 (MCP)
- **Holiday Tool** - 节假日查询 (API)
- **Policy Tool** - 政策检索 (RAG)
- **Forecast Tool** - 统计预测

---

## 实施路线

### Phase 1: 基础架构 (Week 1-2)
- Tool Registry + Database Abstraction
- 简单 LangGraph Workflow
- 迁移现有 API 到 Tool

### Phase 2: Agent 实现 (Week 2-3)
- Intent Classifier + SQL Agent + Diagnosis Agent
- 完整 Workflow 编排

### Phase 3: 高级特性 (Week 3-4)
- RAG 系统 + MCP Mock + SSE Streaming
- Reasoning Traces

### Phase 4: 优化部署 (Week 4-5)
- 性能优化 + Observability
- 生产部署

---

## 参考文档

- 详细路线图: [IMPLEMENTATION_ROADMAP.md](./IMPLEMENTATION_ROADMAP.md)
- 原架构: [ARCHITECTURE.md](./ARCHITECTURE.md)
- PRD: [PRD.md](./PRD.md)
