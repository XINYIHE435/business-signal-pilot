# Phase 2 - 第三方 API 代理配置完成

**日期:** 2026-07-09  
**状态:** ✅ 已适配第三方 API 代理（zhihuiai.top）  

---

## ✅ 已完成的适配

### 1. 配置文件更新
**文件:** `app/core/config.py`

```python
class Settings(BaseSettings):
    anthropic_api_key: str = ""
    ANTHROPIC_BASE_URL: str = "https://cn.zhihuiai.top/"  # 👈 已配置
```

### 2. 客户端更新
所有 Anthropic 客户端已更新使用 `base_url`:

- ✅ `app/core/llm.py` - LLM 客户端
- ✅ `app/agents/intent_classifier.py` - Intent Classifier
- ✅ `app/agents/sql_agent.py` - SQL Agent
- ✅ `check_env.py` - 环境检查脚本

### 3. 新增工具
- ✅ `setup_api_proxy.py` - 交互式 API 配置工具
- ✅ `API_PROXY_SETUP.md` - 详细配置文档

---

## 🚀 快速开始（3步）

### 方法 1: 使用交互式设置工具

```bash
cd backend
python setup_api_proxy.py
```

这会：
1. 提示输入 API Key
2. 自动测试连接
3. 给出下一步指令

### 方法 2: 手动设置

```bash
# 1. 设置 API Key
$env:ANTHROPIC_API_KEY="你的API Key"  # Windows PowerShell

# 2. 验证环境
python check_env.py

# 3. 运行测试
python test_phase2.py
```

---

## 📋 验证清单

### ✅ 配置验证

```bash
# 检查 API Key
python -c "import os; print('API Key:', os.getenv('ANTHROPIC_API_KEY')[:20] if os.getenv('ANTHROPIC_API_KEY') else 'NOT SET')"

# 检查代理地址
python -c "from app.core.config import settings; print('Base URL:', settings.ANTHROPIC_BASE_URL)"
```

### ✅ 连接测试

```bash
# 完整环境检查
python check_env.py
```

**预期输出:**
```
[1] 检查 Anthropic API Key...
    ✓ API Key 已配置: xxx...
    测试 API 连接...
    ✓ API 连接成功！

[2] 检查数据库文件...
    ✓ 数据库文件存在 (XX.XX MB)
    ✓ 数据库连接成功，找到 X 个表

✓ 环境检查通过！所有组件正常。
```

### ✅ 功能测试

```bash
python test_phase2.py
```

**预期输出:**
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

---

## 🔧 常见问题

### Q1: API 连接失败

**错误信息:**
```
Connection error
```

**解决方案:**
1. 确认 API Key 已设置
2. 确认代理地址正确（已配置为 `https://cn.zhihuiai.top/`）
3. 测试网络连接

```bash
# 测试代理可访问性
curl https://cn.zhihuiai.top/

# 如果需要，更换代理地址
# 编辑 backend/app/core/config.py
# ANTHROPIC_BASE_URL: str = "你的代理地址"
```

### Q2: API Key 无效

**错误信息:**
```
401 Unauthorized
```

**解决方案:**
1. 登录 https://cn.zhihuiai.top/ 检查 API Key
2. 确认账户余额充足
3. 重新生成 API Key
4. 重新设置环境变量

### Q3: 模型不支持

**解决方案:**

如果代理不支持 `claude-3-5-sonnet-20241022`，修改模型名称：

```python
# 文件: app/agents/intent_classifier.py 和 sql_agent.py
# 找到 model="claude-3-5-sonnet-20241022"
# 改为: model="claude-3-sonnet-20240229" 或其他支持的模型
```

---

## 📁 相关文件

```
backend/
├── setup_api_proxy.py          # 🆕 交互式 API 设置
├── check_env.py                # ✅ 已更新（支持 base_url）
├── test_phase2.py              # 测试脚本
├── API_PROXY_SETUP.md          # 🆕 详细配置文档
├── PHASE2_FIX_GUIDE.md         # 问题修复指南
├── QUICK_START.md              # 快速开始
└── app/
    ├── core/
    │   ├── config.py            # ✅ 已添加 ANTHROPIC_BASE_URL
    │   └── llm.py               # ✅ 已更新 base_url
    └── agents/
        ├── intent_classifier.py # ✅ 已更新 base_url
        └── sql_agent.py         # ✅ 已更新 base_url
```

---

## 🎯 测试步骤

### 完整测试流程

```bash
# 步骤 1: 进入目录
cd backend

# 步骤 2: 设置 API Key（选择一种方式）
# 方式 A: 交互式
python setup_api_proxy.py

# 方式 B: 手动
$env:ANTHROPIC_API_KEY="你的key"

# 步骤 3: 验证环境
python check_env.py

# 步骤 4: 运行测试
python test_phase2.py

# 步骤 5: (可选) 运行 Pytest
pytest tests/test_orchestrator_v2.py -v
```

### 快速测试（一行命令）

```bash
python check_env.py && python test_phase2.py
```

---

## ✨ 成功标准

测试成功后，您应该看到：

1. ✅ `check_env.py` - "✓ API 连接成功！"
2. ✅ `test_phase2.py` - "✓ 所有测试通过！Phase 2 工作正常。"
3. ✅ Intent 分类正确（不是 fallback 模式）
4. ✅ SQL 生成和执行成功
5. ✅ 完整的推理轨迹

---

## 📊 技术细节

### 代码适配示例

**Before (官方 API):**
```python
client = AsyncAnthropic(api_key=settings.anthropic_api_key)
```

**After (第三方代理):**
```python
client = AsyncAnthropic(
    api_key=settings.anthropic_api_key,
    base_url=settings.ANTHROPIC_BASE_URL  # 👈 添加 base_url
)
```

### 配置优先级

1. 环境变量 `ANTHROPIC_API_KEY` - **必须设置**
2. 配置文件 `ANTHROPIC_BASE_URL` - 已设置为 `https://cn.zhihuiai.top/`
3. 模型名称 - 默认 `claude-3-5-sonnet-20241022`

---

## 🔐 安全提醒

1. ✅ 不要提交 API Key 到 Git
2. ✅ 使用环境变量存储 Key
3. ✅ 定期轮换 API Key
4. ✅ 监控 API 使用量

```bash
# 确认 .env 在 .gitignore 中
echo ".env" >> ../.gitignore
```

---

## 📞 下一步

### 测试通过后

1. **启动完整服务**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **测试 Chat API**
   ```bash
   curl -X POST http://localhost:8000/api/v1/chat/query \
     -H "Content-Type: application/json" \
     -d '{"query": "查询德国站GMV"}'
   ```

3. **Frontend 集成**
   - 在 Next.js 中调用 Chat API
   - 实现聊天界面

### 继续 Phase 3

- RAG 系统实现
- MCP Mock Servers
- SSE Streaming

---

## 📝 总结

**已完成:**
- ✅ 适配第三方 API 代理（zhihuiai.top）
- ✅ 更新所有 Anthropic 客户端使用 base_url
- ✅ 创建交互式设置工具
- ✅ 完整的测试和验证流程

**立即测试:**
```bash
cd backend
python setup_api_proxy.py  # 或手动设置 API Key
python check_env.py
python test_phase2.py
```

**如果所有测试通过，Phase 2 部署完成！** 🎉
