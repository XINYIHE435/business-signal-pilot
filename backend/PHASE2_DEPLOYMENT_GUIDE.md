# Phase 2 部署测试指南

**日期:** 2026-07-09  
**目标:** 测试 Phase 2 实现的 Intent Classifier + SQL Agent  

---

## 快速开始（3分钟）

### 1. 安装依赖

```bash
cd backend

# 激活虚拟环境（如果有）
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate

# 安装新依赖
pip install langgraph==0.2.34 langchain-core==0.3.15 langchain-anthropic==0.3.0
```

### 2. 设置 API Key

```bash
# Windows (PowerShell)
$env:ANTHROPIC_API_KEY="sk-ant-api03-你的key"

# Windows (CMD)
set ANTHROPIC_API_KEY=sk-ant-api03-你的key

# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-api03-你的key"
```

### 3. 运行测试脚本

```bash
python test_phase2.py
```

**预期输出:**
```
============================================================
SignalPilot Phase 2 测试
============================================================

============================================================
测试: 简单数据查询
查询: 查询德国站GMV
============================================================

✓ 意图: data_query
✓ 实体: {"site": "DE", "metric": "gmv"}

响应类型: data_query
成功: True

SQL:
SELECT SUM(gmv) as total_gmv FROM daily_metrics WHERE site='DE'

数据行数: 1
示例数据: {
  "total_gmv": 1234567.89
}

推理轨迹:
  1. intent_classifier - 2026-07-09T...
  2. sql_agent - 2026-07-09T...
  3. synthesizer - 2026-07-09T...
```

---

## 详细测试步骤

### 测试 1: 意图分类（不需要数据库）

```bash
python -c "
import asyncio
from app.agents.intent_classifier import intent_classifier

async def test():
    result = await intent_classifier.classify('为什么德国站GMV下降了？')
    print('Intent:', result['intent'])
    print('Confidence:', result['confidence'])
    print('Entities:', result['entities'])

asyncio.run(test())
"
```

**预期输出:**
```
Intent: root_cause_analysis
Confidence: 0.95
Entities: {'metric': 'gmv', 'site': 'DE'}
```

### 测试 2: SQL Agent（需要数据库）

```bash
python -c "
import asyncio
from app.agents.sql_agent import SQLAgent
from app.tools.database_tool import DatabaseTool
from app.adapters.database import DuckDBAdapter

async def test():
    adapter = DuckDBAdapter('data/signal.db', read_only=True)
    sql_agent = SQLAgent(DatabaseTool(adapter))
    
    result = await sql_agent.generate_and_execute_sql(
        query='查询德国站GMV',
        entities={'site': 'DE'}
    )
    
    print('Success:', result['success'])
    print('SQL:', result.get('sql', '')[:100])
    print('Row count:', result.get('row_count', 0))

asyncio.run(test())
"
```

### 测试 3: 完整 Orchestrator V2

```bash
python -c "
import asyncio
from app.agents.orchestrator_v2 import run_query

async def test():
    result = await run_query('过去7天德国站的GMV')
    print('Intent:', result['intent'])
    print('Success:', result['response'].get('success'))
    print('Data rows:', result['response'].get('row_count', 0))

asyncio.run(test())
"
```

---

## 测试场景清单

### ✅ 场景 1: 简单数据查询
```
查询: "查询德国站GMV"
预期意图: data_query
预期行为: 生成 SQL 并返回数据
```

### ✅ 场景 2: 带条件的查询
```
查询: "过去7天德国站的GMV是多少？"
预期意图: data_query
预期实体: {site: "DE", date_range: "7 days"}
预期行为: 生成带日期过滤的 SQL
```

### ✅ 场景 3: 根因分析
```
查询: "为什么德国站GMV下降了15%？"
预期意图: root_cause_analysis
预期行为: 识别意图，返回提示信息（Diagnosis Agent 未实现）
```

### ✅ 场景 4: 对比分析
```
查询: "对比德国站和英国站的GMV"
预期意图: comparison_analysis
预期行为: 识别意图
```

### ✅ 场景 5: 报告生成
```
查询: "生成本周业务报告"
预期意图: report_generation
预期行为: 识别意图
```

---

## 运行 Pytest 测试套件

```bash
# 运行所有测试
pytest tests/ -v

# 只运行 Phase 2 测试
pytest tests/test_orchestrator_v2.py -v

# 显示详细输出
pytest tests/test_orchestrator_v2.py -v -s
```

**预期结果:**
```
tests/test_orchestrator_v2.py::test_simple_data_query PASSED
tests/test_orchestrator_v2.py::test_data_query_with_date_range PASSED
tests/test_orchestrator_v2.py::test_diagnosis_query PASSED
tests/test_orchestrator_v2.py::test_report_query PASSED
tests/test_orchestrator_v2.py::test_comparison_query PASSED
tests/test_orchestrator_v2.py::test_reasoning_trace PASSED
tests/test_orchestrator_v2.py::test_tool_calls_logged PASSED

============ 7 passed in 15.23s ============
```

---

## 常见问题排查

### Q1: "ANTHROPIC_API_KEY not configured"

**原因:** API Key 未设置

**解决:**
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

**验证:**
```bash
python -c "from app.core.config import settings; print('API Key:', settings.anthropic_api_key[:20] if settings.anthropic_api_key else 'NOT SET')"
```

### Q2: "Database file not found"

**原因:** `data/signal.db` 不存在

**解决:**
```bash
# 生成数据库
python ../data/generate_data.py
```

**验证:**
```bash
ls -lh data/signal.db
```

### Q3: "ModuleNotFoundError: No module named 'langgraph'"

**原因:** 新依赖未安装

**解决:**
```bash
pip install -r requirements.txt
```

### Q4: SQL 执行错误

**原因:** SQL 语法错误或数据库问题

**调试:**
```bash
# 查看详细日志
python test_phase2.py 2>&1 | tee test_output.log

# 检查生成的 SQL
python -c "
import asyncio
from app.agents.orchestrator_v2 import run_query

async def test():
    result = await run_query('查询德国站GMV')
    print('SQL:', result['response'].get('sql'))
    print('Error:', result['response'].get('error'))

asyncio.run(test())
"
```

### Q5: Intent 分类不准确

**原因:** 使用 fallback 模式（关键词匹配）

**解决:** 确保 Claude API Key 已配置

**验证:**
```bash
python -c "
from app.agents.intent_classifier import IntentClassifierAgent
agent = IntentClassifierAgent()
print('Claude client available:', agent.client is not None)
"
```

---

## 性能基准

| 操作 | 预期时间 | 说明 |
|------|----------|------|
| Intent Classification | < 2s | Claude API 调用 |
| SQL Generation | < 3s | Claude + Schema 检索 |
| SQL Execution | < 500ms | DuckDB 查询 |
| **端到端查询** | **< 10s** | 完整流程 |

---

## 监控和日志

### 查看推理轨迹

```python
import asyncio
from app.agents.orchestrator_v2 import run_query
import json

async def test():
    result = await run_query('查询德国站GMV')
    
    print("Reasoning Trace:")
    print(json.dumps(result['reasoning_trace'], indent=2, ensure_ascii=False))

asyncio.run(test())
```

### 查看 Tool 调用

```python
async def test():
    result = await run_query('查询德国站GMV')
    
    print("Tool Calls:")
    for call in result['tool_calls']:
        print(f"  - {call['tool']}: {call.get('success', 'N/A')}")

asyncio.run(test())
```

---

## 下一步

### ✅ Phase 2 测试通过后

1. **集成到 Frontend** - 创建 `/api/v1/chat` endpoint
2. **添加 Diagnosis Agent** - 完成根因分析功能
3. **开始 Phase 3** - RAG + MCP + Streaming

### 如果测试失败

1. 检查 API Key 配置
2. 确认数据库文件存在
3. 查看详细错误日志
4. 参考上面的"常见问题排查"

---

## 成功标准

- [ ] `test_phase2.py` 所有场景通过
- [ ] Pytest 测试套件通过
- [ ] Intent 分类准确率 >80%
- [ ] SQL 生成成功率 >90%
- [ ] 推理轨迹完整记录

**所有标准达成后，Phase 2 部署测试完成！** ✅

---

## 快速验证命令

```bash
# 一键测试所有功能
python test_phase2.py && pytest tests/test_orchestrator_v2.py -v

# 如果成功，你会看到：
# "✓ 所有测试通过！Phase 2 工作正常。"
# "============ 7 passed ============"
```

**准备好了吗？运行测试！** 🚀
