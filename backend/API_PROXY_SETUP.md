# 第三方 API 代理配置指南

**适用于:** 使用第三方 Claude API 代理服务（如 zhihuiai.top）

---

## 🔧 配置步骤

### 1. 设置环境变量

```bash
# Windows PowerShell
$env:ANTHROPIC_API_KEY="你的API Key"

# Linux/Mac
export ANTHROPIC_API_KEY="你的API Key"
```

**注意:** API Key 格式可能与官方不同，使用代理提供的完整 key 即可。

### 2. 验证配置

SignalPilot 已经配置了默认的代理地址：

```python
# backend/app/core/config.py
ANTHROPIC_BASE_URL: str = "https://cn.zhihuiai.top/"
```

### 3. 测试连接

```bash
cd backend
python check_env.py
```

**预期输出:**
```
[1] 检查 Anthropic API Key...
    ✓ API Key 已配置: xxx...
    测试 API 连接...
    ✓ API 连接成功！
```

---

## 🌐 使用不同的代理服务

如果您使用其他代理服务，修改 `backend/app/core/config.py`:

```python
class Settings(BaseSettings):
    # AI 配置
    anthropic_api_key: str = ""
    ANTHROPIC_BASE_URL: str = "https://你的代理地址/"  # 👈 修改这里
    # ...
```

**常见代理地址:**
- zhihuiai.top: `https://cn.zhihuiai.top/`
- api2d.com: `https://api2d.com/anthropic/`
- 其他: 参考服务提供商文档

---

## 🔍 验证代理连接

### 方法 1: 使用环境检查脚本

```bash
python check_env.py
```

### 方法 2: 手动测试

```python
from anthropic import Anthropic
from app.core.config import settings

client = Anthropic(
    api_key=settings.anthropic_api_key,
    base_url=settings.ANTHROPIC_BASE_URL
)

response = client.messages.create(
    model="claude-3-5-sonnet-20241022",
    max_tokens=10,
    messages=[{"role": "user", "content": "test"}]
)

print("✓ API 连接成功!")
print(response.content[0].text)
```

---

## ⚠️ 常见问题

### Q1: Connection error

**原因:** 
- API Key 未设置
- 代理地址不正确
- 网络连接问题

**解决:**
```bash
# 1. 确认 API Key
echo $env:ANTHROPIC_API_KEY  # Windows
echo $ANTHROPIC_API_KEY      # Linux/Mac

# 2. 确认代理地址
python -c "from app.core.config import settings; print(settings.ANTHROPIC_BASE_URL)"

# 3. 测试网络
curl https://cn.zhihuiai.top/
```

### Q2: 401 Unauthorized

**原因:** API Key 无效或过期

**解决:**
- 登录代理服务网站检查 API Key
- 确认账户余额充足
- 重新生成 API Key

### Q3: 模型不支持

**原因:** 某些代理服务可能不支持所有模型

**解决:**
修改 `backend/app/agents/intent_classifier.py` 和 `sql_agent.py` 中的模型名称：

```python
# 从
model="claude-3-5-sonnet-20241022"

# 改为代理支持的模型，例如
model="claude-3-5-sonnet-latest"
model="claude-3-sonnet-20240229"
```

---

## ✅ 已更新的文件

SignalPilot 已经适配第三方代理，以下文件已更新 base_url 配置：

1. ✅ `app/core/config.py` - 添加 `ANTHROPIC_BASE_URL` 配置
2. ✅ `app/core/llm.py` - 使用 base_url
3. ✅ `app/agents/intent_classifier.py` - 使用 base_url
4. ✅ `app/agents/sql_agent.py` - 使用 base_url
5. ✅ `check_env.py` - 验证使用 base_url

---

## 🚀 快速开始

```bash
# 1. 设置 API Key
$env:ANTHROPIC_API_KEY="你的key"

# 2. 验证环境
python check_env.py

# 3. 运行测试
python test_phase2.py
```

---

## 📝 代理服务对比

| 服务 | 优点 | 缺点 | 推荐场景 |
|------|------|------|----------|
| **官方 API** | 稳定、全功能 | 需要国际支付 | 生产环境 |
| **zhihuiai.top** | 国内可用、支持支付宝 | 可能有延迟 | 开发测试 |
| **api2d.com** | 支持多种模型 | 需要充值 | 开发测试 |

---

## 🔐 安全建议

1. **不要提交 API Key 到 Git**
   ```bash
   # 确认 .env 在 .gitignore 中
   echo ".env" >> .gitignore
   ```

2. **使用环境变量**
   ```bash
   # 不要硬编码 API Key
   # ✗ api_key = "sk-ant-..."
   # ✓ api_key = os.getenv("ANTHROPIC_API_KEY")
   ```

3. **定期轮换 Key**
   - 定期更换 API Key
   - 监控 API 使用量
   - 设置使用限额

---

## 📞 获取帮助

### 检查配置
```bash
python -c "
from app.core.config import settings
print('API Key:', settings.anthropic_api_key[:20] if settings.anthropic_api_key else 'NOT SET')
print('Base URL:', settings.ANTHROPIC_BASE_URL)
"
```

### 完整测试
```bash
python check_env.py && python test_phase2.py
```

---

**配置完成后，运行测试验证一切正常！** 🎉
