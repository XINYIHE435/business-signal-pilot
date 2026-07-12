# Phase 2 问题修复指南

**日期:** 2026-07-09  
**状态:** 问题已修复，请重新测试  

---

## 🔧 已修复的问题

### ✅ 问题 1: API 连接错误
**症状:** `Connection error` - Intent Classifier 无法连接 Claude API

**根因:** 
- API Key 未正确设置
- 或网络连接问题

**修复:**
1. 改进了错误处理和日志
2. 提供更详细的错误信息
3. Fallback 模式现在工作正常

### ✅ 问题 2: Database Tool 未找到
**症状:** `database_tool_not_found` - SQL Agent 找不到数据库工具

**根因:**
- Tool Registry 初始化时机问题
- SQL Agent 依赖 registry 中的工具

**修复:**
1. SQL Agent 节点现在直接创建 Database Adapter
2. 不再依赖 Tool Registry
3. 改进了数据库路径解析

---

## 🚀 重新测试步骤

### 1️⃣ 运行环境检查（新增）

```bash
cd backend
python check_env.py
```

**这会检查:**
- ✓ API Key 是否配置
- ✓ API 连接是否正常
- ✓ 数据库文件是否存在
- ✓ 依赖是否安装

**预期输出:**
```
✓ 环境检查通过！所有组件正常。
```

### 2️⃣ 设置 API Key（如果还没设置）

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-api03-你的完整key"

# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-api03-你的完整key"
```

**验证设置:**
```bash
# Windows
echo $env:ANTHROPIC_API_KEY

# Linux/Mac
echo $ANTHROPIC_API_KEY
```

### 3️⃣ 运行测试

```bash
python test_phase2.py
```

**现在应该看到:**
```
✓ 意图: data_query
✓ 实体: {"site": "DE"}

响应类型: data_query
成功: True

SQL:
SELECT SUM(gmv) as total_gmv FROM daily_metrics WHERE site='DE'

数据行数: 1
```

---

## 📋 常见问题排查

### Q1: API Key 设置了但还是 Connection error

**可能原因:**
1. 网络无法访问 api.anthropic.com
2. 需要代理设置
3. API Key 格式错误

**解决方案:**

```bash
# 1. 测试网络连接
curl https://api.anthropic.com/v1/messages

# 2. 如果需要代理
export HTTP_PROXY="http://proxy:port"
export HTTPS_PROXY="http://proxy:port"

# 3. 验证 API Key 格式
# 应该以 "sk-ant-api03-" 开头
```

**测试 API:**
```bash
python -c "
from anthropic import Anthropic
import os

api_key = os.getenv('ANTHROPIC_API_KEY')
print('API Key:', api_key[:20] if api_key else 'NOT SET')

if api_key:
    try:
        client = Anthropic(api_key=api_key)
        response = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=10,
            messages=[{'role': 'user', 'content': 'test'}]
        )
        print('✓ API 连接成功!')
    except Exception as e:
        print(f'✗ API 连接失败: {e}')
"
```

### Q2: 数据库文件不存在

**检查路径:**
```bash
# 当前应该在 backend/ 目录
pwd

# 检查数据库文件
ls -lh ../data/signal.db
```

**生成数据库:**
```bash
cd ../data
python generate_data.py
cd ../backend
```

### Q3: 使用 Fallback 模式（关键词匹配）

**现象:**
```
⚠️  警告: ANTHROPIC_API_KEY 未配置
将使用 fallback 模式（关键词匹配）进行测试
```

**影响:**
- 意图分类准确率降低
- 仍然可以测试基本功能
- SQL 生成将失败（需要 Claude API）

**建议:** 设置 API Key 以获得完整功能

### Q4: SQL 生成失败

**检查:**
1. API Key 是否配置
2. 数据库文件是否存在
3. 查看详细错误日志

```bash
# 详细日志
python test_phase2.py 2>&1 | tee test.log
```

---

## 🔍 调试命令

### 测试 API 连接
```bash
python check_env.py
```

### 测试 Intent Classifier
```bash
python -c "
import asyncio
from app.agents.intent_classifier import intent_classifier

async def test():
    result = await intent_classifier.classify('查询德国站GMV')
    print('Intent:', result['intent'])
    print('Confidence:', result['confidence'])
    print('Entities:', result['entities'])

asyncio.run(test())
"
```

### 测试 SQL Agent
```bash
python -c "
import asyncio
from pathlib import Path
from app.agents.sql_agent import SQLAgent
from app.tools.database_tool import DatabaseTool
from app.adapters.database import DuckDBAdapter

async def test():
    project_root = Path('.')
    db_path = project_root / 'data' / 'signal.db'
    
    if not db_path.exists():
        print(f'✗ 数据库不存在: {db_path}')
        return
    
    adapter = DuckDBAdapter(str(db_path), read_only=True)
    sql_agent = SQLAgent(DatabaseTool(adapter))
    
    result = await sql_agent.generate_and_execute_sql(
        query='查询德国站GMV',
        entities={'site': 'DE'}
    )
    
    print('Success:', result['success'])
    if result['success']:
        print('SQL:', result.get('sql', '')[:100])
        print('Row count:', result.get('row_count', 0))
    else:
        print('Error:', result.get('error'))
    
    adapter.close()

asyncio.run(test())
"
```

### 测试完整流程
```bash
python -c "
import asyncio
from app.agents.orchestrator_v2 import run_query

async def test():
    result = await run_query('查询德国站GMV')
    
    print('Intent:', result['intent'])
    print('Success:', result['response'].get('success'))
    print('Response type:', result['response']['type'])
    
    if result['response'].get('error'):
        print('Error:', result['response']['error'])

asyncio.run(test())
"
```

---

## ✅ 验证修复成功

运行以下命令，如果都成功则修复完成：

```bash
# 1. 环境检查
python check_env.py
# 预期: "✓ 环境检查通过！"

# 2. Phase 2 测试
python test_phase2.py
# 预期: "✓ 所有测试通过！"

# 3. Pytest 测试
pytest tests/test_orchestrator_v2.py -v
# 预期: "7 passed"
```

---

## 📞 仍然有问题？

### 检查列表

- [ ] API Key 已正确设置（`echo $ANTHROPIC_API_KEY`）
- [ ] API Key 格式正确（以 `sk-ant-api03-` 开头）
- [ ] 网络可以访问 api.anthropic.com
- [ ] 数据库文件存在（`ls -lh ../data/signal.db`）
- [ ] 依赖已安装（`pip list | grep langgraph`）
- [ ] 当前在 backend/ 目录（`pwd`）

### 完整重置

如果还是有问题，尝试完整重置：

```bash
# 1. 重新安装依赖
pip install -r requirements.txt --force-reinstall

# 2. 重新生成数据库
cd ../data
python generate_data.py
cd ../backend

# 3. 验证环境
python check_env.py

# 4. 运行测试
python test_phase2.py
```

---

## 🎯 成功标准

修复成功后，您应该看到：

```
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

============================================================
测试完成: 5/5 成功
============================================================

✓ 所有测试通过！Phase 2 工作正常。
```

**如果看到以上输出，恭喜！Phase 2 已成功部署！** 🎉

---

## 📝 修复总结

**修改的文件:**
1. `app/agents/intent_classifier.py` - 改进错误处理
2. `app/agents/sql_agent.py` - 修复 database tool 查找问题
3. `app/api/chat.py` - 改进工具初始化
4. `check_env.py` - 新增环境检查脚本（NEW）

**现在重新测试:**
```bash
python check_env.py && python test_phase2.py
```

🚀 **祝测试成功！**
