# Phase 2 部署就绪 - 快速开始

**状态:** ✅ 可以立即测试  
**日期:** 2026-07-09  

---

## 🚀 3 步快速开始

### 1️⃣ 安装依赖（1分钟）

```bash
cd backend
pip install langgraph==0.2.34 langchain-core==0.3.15 langchain-anthropic==0.3.0
```

### 2️⃣ 设置 API Key（30秒）

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="sk-ant-你的key"

# Linux/Mac
export ANTHROPIC_API_KEY="sk-ant-你的key"
```

### 3️⃣ 运行测试（1分钟）

```bash
python test_phase2.py
```

**预期看到:**
```
✓ 所有测试通过！Phase 2 工作正常。
```

---

## 📡 启动完整服务

### 启动 Backend API

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**访问:**
- API 文档: http://localhost:8000/docs
- Health Check: http://localhost:8000/health
- Chat API: http://localhost:8000/api/v1/chat/query

### 测试 Chat API

```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "查询德国站GMV",
    "session_id": "test_session"
  }'
```

**预期响应:**
```json
{
  "success": true,
  "intent": "data_query",
  "entities": {"site": "DE", "metric": "gmv"},
  "response": {
    "type": "data_query",
    "success": true,
    "data": [...],
    "sql": "SELECT SUM(gmv) as total_gmv FROM daily_metrics WHERE site='DE'",
    "row_count": 1,
    "message": "查询成功，返回 1 行数据"
  },
  "reasoning_trace": [...],
  "tool_calls": [...]
}
```

---

## 🧪 测试清单

### ✅ 必须通过的测试

- [ ] `python test_phase2.py` - 所有场景通过
- [ ] `pytest tests/test_orchestrator_v2.py -v` - 单元测试通过
- [ ] Backend 启动成功（http://localhost:8000/docs）
- [ ] Chat API 返回正确响应

### ✅ 功能验证

- [ ] 意图分类准确（测试 5 种意图）
- [ ] SQL 生成正确（查看生成的 SQL）
- [ ] 数据查询成功（返回实际数据）
- [ ] 推理轨迹完整（3+ 节点记录）
- [ ] 错误处理正常（故意输错查询）

---

## 📊 测试场景

### 场景 1: 简单查询
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "查询德国站GMV"}'
```

### 场景 2: 带条件查询
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "过去7天德国站的GMV是多少？"}'
```

### 场景 3: 根因分析
```bash
curl -X POST http://localhost:8000/api/v1/chat/query \
  -H "Content-Type: application/json" \
  -d '{"query": "为什么德国站GMV下降了？"}'
```

---

## ⚡ Frontend 集成示例

### JavaScript/TypeScript

```typescript
// lib/api.ts
export const chatAPI = {
  query: async (query: string, sessionId: string = 'default') => {
    const response = await fetch('http://localhost:8000/api/v1/chat/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, session_id: sessionId })
    });
    return response.json();
  }
};

// 使用
const result = await chatAPI.query('查询德国站GMV');
console.log('Intent:', result.intent);
console.log('Data:', result.response.data);
```

### React 组件示例

```tsx
'use client';

import { useState } from 'react';
import { chatAPI } from '@/lib/api';

export function ChatInterface() {
  const [query, setQuery] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      const data = await chatAPI.query(query);
      setResult(data);
    } catch (error) {
      console.error('Query failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="输入查询..."
        />
        <button disabled={loading}>
          {loading ? '查询中...' : '提交'}
        </button>
      </form>

      {result && (
        <div>
          <p>意图: {result.intent}</p>
          <p>成功: {result.success ? '✓' : '✗'}</p>
          {result.response.data && (
            <pre>{JSON.stringify(result.response.data, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## 🔧 故障排查

### 问题 1: API Key 未配置
```bash
# 检查
python -c "from app.core.config import settings; print('API Key:', settings.anthropic_api_key[:20] if settings.anthropic_api_key else 'NOT SET')"

# 解决
export ANTHROPIC_API_KEY="your-key"
```

### 问题 2: 数据库文件不存在
```bash
# 检查
ls -lh data/signal.db

# 解决
python data/generate_data.py
```

### 问题 3: 依赖缺失
```bash
# 检查
pip list | grep langgraph

# 解决
pip install -r requirements.txt
```

### 问题 4: 端口被占用
```bash
# 更换端口
uvicorn app.main:app --reload --port 8001
```

---

## 📁 关键文件位置

```
backend/
├── test_phase2.py                    # 👈 快速测试脚本
├── PHASE2_DEPLOYMENT_GUIDE.md        # 👈 详细部署指南
├── PHASE2_COMPLETION.md              # 📄 完成报告
├── app/
│   ├── main.py                       # ✅ 已注册 Chat API
│   ├── api/
│   │   └── chat.py                   # 👈 Chat API endpoint
│   └── agents/
│       ├── orchestrator_v2.py        # 👈 主 Orchestrator
│       ├── intent_classifier.py      # 🧠 意图分类
│       └── sql_agent.py              # 💾 SQL 生成
└── tests/
    └── test_orchestrator_v2.py       # 🧪 测试套件
```

---

## ✅ 成功标准

所有以下检查通过即可认为 Phase 2 部署成功：

1. ✅ `python test_phase2.py` 显示 "所有测试通过"
2. ✅ `pytest tests/test_orchestrator_v2.py` 全部 PASSED
3. ✅ Backend API 可以访问 http://localhost:8000/docs
4. ✅ Chat API 返回正确的意图和 SQL
5. ✅ 推理轨迹完整记录

---

## 🎯 下一步

### Phase 2 测试通过后：

1. **Frontend 集成** - 在 Next.js 中调用 Chat API
2. **完成 Diagnosis Agent** - 实现根因分析
3. **开始 Phase 3** - RAG + MCP + Streaming

### 立即可做：

```bash
# 1. 运行快速测试
python test_phase2.py

# 2. 启动 Backend
uvicorn app.main:app --reload

# 3. 在浏览器打开
# http://localhost:8000/docs

# 4. 测试 Chat API
# POST /api/v1/chat/query
```

---

## 📞 需要帮助？

### 常用命令

```bash
# 查看日志
python test_phase2.py 2>&1 | tee test.log

# 详细测试
pytest tests/ -v -s

# 检查 API 健康
curl http://localhost:8000/api/v1/chat/health
```

### 文档

- **详细部署指南:** `PHASE2_DEPLOYMENT_GUIDE.md`
- **完成报告:** `PHASE2_COMPLETION.md`
- **实施路线图:** `../docs/IMPLEMENTATION_ROADMAP.md`

---

**准备好了吗？开始测试 Phase 2！** 🚀

```bash
cd backend && python test_phase2.py
```
