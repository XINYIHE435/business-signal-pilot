# SignalPilot 企业级架构实施路线图

**版本:** 1.0  
**日期:** 2026-07-09  
**预计工期:** 4-5 周  

---

## 概览

将 SignalPilot 从 MVP 升级为企业级 AI Agent 平台，分 4 个阶段实施：

| 阶段 | 重点 | 工期 | 产出 |
|------|------|------|------|
| **Phase 1** | 基础架构 | Week 1-2 | LangGraph + Tool Registry |
| **Phase 2** | Agent 实现 | Week 2-3 | 核心 Agents |
| **Phase 3** | 高级特性 | Week 3-4 | MCP + RAG + Streaming |
| **Phase 4** | 优化部署 | Week 4-5 | Observability + Production |

---

## Phase 1: 基础架构搭建 (Week 1-2)

### 目标
建立 LangGraph 编排引擎和 Tool Registry 基础架构

### 任务清单

#### 1.1 安装依赖
```bash
cd backend
pip install langgraph==0.2.0
pip install langchain-core==0.3.0
pip install chromadb==0.5.0
pip install sentence-transformers==3.0.0
pip install langsmith==0.2.0  # 可选
```

#### 1.2 创建目录结构
```bash
mkdir -p app/agents
mkdir -p app/tools
mkdir -p app/adapters/database
mkdir -p app/adapters/mcp
mkdir -p app/rag
mkdir -p app/rag/knowledge_base
```

#### 1.3 实现 Tool Registry
- [ ] 创建 `app/tools/registry.py`
- [ ] 定义 `BaseTool` 抽象类
- [ ] 实现 `ToolRegistry` 类
- [ ] 编写单元测试

#### 1.4 实现 Database Abstraction
- [ ] 创建 `app/adapters/database/base.py` (DatabaseAdapter 接口)
- [ ] 实现 `app/adapters/database/duckdb.py` (DuckDBAdapter)
- [ ] 实现 `app/adapters/database/postgres.py` (PostgreSQLAdapter - 占位)
- [ ] 创建 `app/tools/database_tool.py`
- [ ] 编写测试

#### 1.5 迁移现有 Dashboard API 到 Tool
- [ ] 将 `app/api/dashboard.py` 中的 SQL 逻辑提取到 Tools
- [ ] 创建 `KPITool`, `TrendTool`, `AnomalyTool`
- [ ] 测试工具独立运行

#### 1.6 实现基础 LangGraph Workflow
- [ ] 创建 `app/agents/orchestrator.py`
- [ ] 定义 `AgentState` TypedDict
- [ ] 实现简单的 StateGraph (intent → sql → synthesizer)
- [ ] 测试端到端流程

### 验收标准
- [ ] Tool Registry 可以注册和调用工具
- [ ] Database Tool 通过抽象层执行 SQL
- [ ] 简单的 LangGraph workflow 可以运行
- [ ] 现有 Dashboard API 功能不受影响

---

## Phase 2: Agent 实现 (Week 2-3)

### 目标
实现核心 Agents: Intent Classifier, SQL Agent, Diagnosis Agent

### 任务清单

#### 2.1 Intent Classifier Agent
- [ ] 创建 `app/agents/intent_classifier.py`
- [ ] 实现 intent_classifier_node
- [ ] 使用 Claude Tool Calling 进行结构化输出
- [ ] 测试意图分类准确率 (>80%)

#### 2.2 SQL Agent (带 RAG)
- [ ] 创建 `app/agents/sql_agent.py`
- [ ] 实现 RAG schema 检索
- [ ] 实现 SQL 生成和执行
- [ ] 实现 SQL 验证和错误重试
- [ ] 测试常见查询场景

#### 2.3 Diagnosis Agent
- [ ] 创建 `app/agents/diagnosis_agent.py`
- [ ] 实现异常检测逻辑
- [ ] 实现贡献度分解 (contribution analysis)
- [ ] 实现假设生成和证据收集
- [ ] 实现根因排序
- [ ] 测试诊断准确性

#### 2.4 Synthesizer Agent
- [ ] 创建 `app/agents/synthesizer.py`
- [ ] 实现结果聚合
- [ ] 实现响应格式化
- [ ] 测试输出质量

#### 2.5 完整 Workflow
- [ ] 更新 `orchestrator.py` 连接所有 Agents
- [ ] 添加条件路由逻辑
- [ ] 添加错误处理节点
- [ ] 测试端到端场景

### 验收标准
- [ ] 能正确分类 5 种常见意图
- [ ] SQL Agent 生成的 SQL 语法正确率 >90%
- [ ] Diagnosis Agent 能识别 top 3 根因
- [ ] 完整 workflow 端到端测试通过

---

## Phase 3: 高级特性 (Week 3-4)

### 目标
实现 MCP 集成、RAG 系统、SSE Streaming

### 任务清单

#### 3.1 RAG 系统
- [ ] 创建 `app/rag/retriever.py`
- [ ] 初始化 ChromaDB collections
- [ ] 准备 Schema 文档 (JSON)
- [ ] 准备 Metrics 定义 (JSON)
- [ ] 准备 Policy 文档 (Markdown)
- [ ] 实现文档嵌入和检索
- [ ] 测试检索质量

#### 3.2 MCP Client 接口
- [ ] 创建 `app/adapters/mcp/base.py` (MCPServerAdapter)
- [ ] 创建 `app/adapters/mcp/mock.py` (Mock Salesforce)
- [ ] 创建 `app/tools/campaign_tool.py` (基于 MCP)
- [ ] 测试 MCP 工具调用

#### 3.3 SSE Streaming
- [ ] 创建 `app/api/chat.py` (新 API)
- [ ] 实现 SSE endpoint
- [ ] LangGraph streaming 集成
- [ ] Frontend SSE 消费端
- [ ] 测试流式输出

#### 3.4 Reasoning Traces
- [ ] 在每个节点记录推理过程
- [ ] 创建 Traces API
- [ ] Frontend Traces UI 组件
- [ ] 测试可观测性

### 验收标准
- [ ] RAG 检索相关 Schema top-3 准确率 >80%
- [ ] MCP Mock 工具可以正常调用
- [ ] SSE 流式输出延迟 <500ms
- [ ] Reasoning Traces 完整记录所有步骤

---

## Phase 4: 优化与部署 (Week 4-5)

### 目标
性能优化、错误处理、生产部署

### 任务清单

#### 4.1 性能优化
- [ ] 实现 LLM 响应缓存
- [ ] 实现 SQL 结果缓存
- [ ] 优化 RAG 检索性能
- [ ] 并行化 Tool 调用
- [ ] 性能测试 (目标: <10s)

#### 4.2 错误处理
- [ ] 实现 Tool 调用重试机制
- [ ] 实现 LLM 超时处理
- [ ] 实现 Fallback 策略
- [ ] 完善错误日志

#### 4.3 Observability
- [ ] 集成 LangSmith (可选)
- [ ] 实现自定义 Metrics
- [ ] 实现 Alert 机制
- [ ] Dashboard 监控页面

#### 4.4 部署
- [ ] 更新 requirements.txt
- [ ] 更新 Dockerfile
- [ ] 配置环境变量
- [ ] 部署到 Fly.io
- [ ] 测试生产环境

### 验收标准
- [ ] 端到端响应时间 <10s (p95)
- [ ] 错误率 <5%
- [ ] 生产环境稳定运行 24h+
- [ ] Observability dashboard 可用

---

## 技术债务清理

### 必须移除
- [x] `app/api/dashboard.py` 中的硬编码 SQL → 迁移到 DatabaseTool
- [ ] 简单的 LLM 客户端 → 替换为 LangGraph 调用
- [ ] 直接数据库访问 → 通过 Database Abstraction

### 新增依赖
```txt
langgraph==0.2.0
langchain-core==0.3.0
chromadb==0.5.0
sentence-transformers==3.0.0
langsmith==0.2.0
```

---

## 风险与缓解

| 风险 | 影响 | 概率 | 缓解措施 |
|------|------|------|----------|
| LangGraph 学习曲线 | 进度延迟 | 高 | 从简单 workflow 开始，逐步复杂化 |
| RAG 检索质量低 | 诊断准确率下降 | 中 | 准备高质量文档，调整 top-k |
| LLM API 成本 | 预算超支 | 中 | Prompt 缓存 + 结果缓存 |
| 性能不达标 | 用户体验差 | 低 | 并行化 + 缓存 + Streaming |

---

## 下一步行动

### 立即开始 (今天)
1. 安装 LangGraph 相关依赖
2. 创建目录结构
3. 实现 Tool Registry 基类

### 本周完成
- Phase 1.1 - 1.4 (基础架构)
- 第一个可运行的 LangGraph workflow

### 里程碑
- **Week 1 End**: Tool Registry + Database Abstraction
- **Week 2 End**: 核心 Agents 实现
- **Week 3 End**: MCP + RAG + Streaming
- **Week 4 End**: 生产就绪

---

**准备好开始实施了吗？**
