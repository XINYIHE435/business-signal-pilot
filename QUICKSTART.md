# 🚀 SignalPilot 快速启动指南

欢迎使用 SignalPilot！本指南将帮助你在 **10 分钟内**从零开始运行整个项目。

---

## 📋 前置要求

### 必需软件

| 软件 | 最低版本 | 推荐版本 | 下载链接 |
|------|---------|---------|---------|
| **Python** | 3.11 | 3.11+ | [python.org](https://www.python.org/downloads/) |
| **Node.js** | 18 | 20+ | [nodejs.org](https://nodejs.org/) |
| **pnpm** | 8.0 | 9.0+ | `npm install -g pnpm` |

### 验证安装

```bash
# 检查 Python 版本
python --version
# 应该显示: Python 3.11.x 或更高

# 检查 Node.js 版本
node --version
# 应该显示: v18.x.x 或更高

# 检查 pnpm 版本
pnpm --version
# 应该显示: 8.x.x 或更高

# 如果 pnpm 未安装
npm install -g pnpm
```

---

## 🎯 快速启动（10 分钟）

### Step 1: 获取项目代码

```bash
# 方法 1: 使用 Git
git clone https://github.com/yourusername/business-signal-pilot.git
cd business-signal-pilot

# 方法 2: 下载 ZIP
# 解压后进入目录
cd business-signal-pilot
```

### Step 2: 配置 API Key（可选）

**注意**: Dashboard 功能不需要 API Key，AI Chat 功能需要。

```bash
# 进入 backend 目录
cd backend

# 创建 .env 文件
echo "ANTHROPIC_API_KEY=your_api_key_here" > .env
echo "ANTHROPIC_BASE_URL=https://api.anthropic.com" >> .env

# 如果没有 API Key，可以跳过此步骤
# Dashboard 功能仍然可以正常使用
```

### Step 3: 启动 Backend（终端 1）

```bash
# 进入 backend 目录
cd backend

# 安装 Python 依赖（首次运行）
pip install fastapi uvicorn structlog anthropic pydantic-settings duckdb langgraph langchain-anthropic

# 启动 Backend 服务器
uvicorn app.main:app --reload --port 8000
```

**预期输出**:
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
[info] application_starting version=1.0.0
[info] database_connected path=../data/signal.db schema_version=v2
[info] max_date_fetched max_date=2026-07-12
```

**验证 Backend**:
```bash
# 在新终端窗口测试
curl http://localhost:8000/health

# 预期返回：
# {
#   "status": "ok",
#   "database_connected": true,
#   "llm_available": true,
#   "version": "1.0.0"
# }
```

### Step 4: 启动 Frontend（终端 2）

打开**新的终端窗口**:

```bash
# 进入 frontend 目录
cd frontend

# 安装 Node.js 依赖（首次运行）
pnpm install

# 启动 Frontend 服务器
pnpm dev
```

**预期输出**:
```
▲ Next.js 15.1.8 (Turbopack)
- Local:        http://localhost:3000
- Network:      http://192.168.x.x:3000

✓ Starting...
✓ Ready in 2.1s
```

### Step 5: 访问应用 🎉

**Frontend Dashboard**:
- 地址: http://localhost:3000
- 功能: KPI 监控、趋势分析、异常检测

**AI Chat**:
- 地址: http://localhost:3000/chat
- 功能: 自然语言查询（需要 API Key）

**Backend API**:
- API 文档: http://localhost:8000/docs
- 健康检查: http://localhost:8000/health
- Business Date: http://localhost:8000/api/v1/dashboard/business-date

---

## 🔧 详细安装指南

### Backend 详细步骤

#### 1. 创建 Python 虚拟环境（推荐）

```bash
cd backend

# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# Windows:
venv\Scripts\activate

# macOS/Linux:
source venv/bin/activate

# 验证虚拟环境
which python  # macOS/Linux
where python  # Windows
# 应该显示虚拟环境中的 Python 路径
```

#### 2. 安装依赖

**方法 1: 使用 requirements.txt（推荐）**

```bash
pip install -r requirements.txt
```

**方法 2: 手动安装核心依赖**

```bash
pip install \
    fastapi==0.138.0 \
    uvicorn==0.49.0 \
    structlog==26.1.0 \
    anthropic \
    pydantic-settings \
    duckdb \
    langgraph \
    langchain-anthropic \
    httpx \
    pytest \
    pytest-asyncio
```

#### 3. 验证数据库

```bash
# 检查数据库文件
ls -lh ../data/signal.db

# 预期输出: signal.db 文件约 15-20 MB

# 验证数据内容
python -c "
import duckdb
conn = duckdb.connect('../data/signal.db')
print('✅ daily_metrics:', conn.execute('SELECT COUNT(*) FROM daily_metrics').fetchone()[0], 'rows')
print('✅ Business Date:', conn.execute('SELECT MAX(date) FROM daily_metrics').fetchone()[0])
print('✅ Sites:', conn.execute('SELECT COUNT(DISTINCT site) FROM daily_metrics').fetchone()[0])
print('✅ L1 Categories:', conn.execute('SELECT COUNT(DISTINCT category_l1) FROM daily_metrics').fetchone()[0])
conn.close()
"
```

**预期输出**:
```
✅ daily_metrics: 593808 rows
✅ Business Date: 2026-07-12
✅ Sites: 10
✅ L1 Categories: 20
```

#### 4. 配置环境变量

```bash
# 创建 .env 文件
cat > .env << 'EOF'
# Anthropic API (用于 AI Chat 功能)
ANTHROPIC_API_KEY=your_api_key_here
ANTHROPIC_BASE_URL=https://api.anthropic.com

# 数据库配置
DATABASE_PATH=../data/signal.db

# 日志级别
LOG_LEVEL=INFO
EOF

# 编辑 .env 文件，替换 your_api_key_here
```

**注意**: 
- Dashboard 功能不需要 API Key
- AI Chat 功能需要 Anthropic API Key
- 可以在 https://console.anthropic.com/ 获取 API Key

#### 5. 启动服务器

```bash
# 方法 1: 使用 uvicorn（推荐）
uvicorn app.main:app --reload --port 8000

# 方法 2: 使用 Python 模块
python -m app.main

# 方法 3: 指定 host 和 port
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**测试 API**:
```bash
# 1. 健康检查
curl http://localhost:8000/health

# 2. 获取 Business Date
curl http://localhost:8000/api/v1/dashboard/business-date
# 预期: {"business_date": "2026-07-12", ...}

# 3. 获取 KPI
curl "http://localhost:8000/api/v1/dashboard/kpis?site=DE&days=7"

# 4. 获取趋势数据
curl "http://localhost:8000/api/v1/dashboard/trends?site=US&days=30"
```

---

### Frontend 详细步骤

#### 1. 安装依赖

```bash
cd frontend

# 使用 pnpm（推荐，更快）
pnpm install

# 或使用 npm
npm install

# 或使用 yarn
yarn install
```

**常见依赖**:
```json
{
  "next": "^15.1.8",
  "react": "^19.0.0",
  "react-dom": "^19.0.0",
  "swr": "^2.x",
  "recharts": "^2.x",
  "lucide-react": "^0.x",
  "tailwindcss": "^3.x"
}
```

#### 2. 配置环境变量

```bash
# 创建 .env.local 文件
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local

# 验证配置
cat .env.local
```

#### 3. 启动开发服务器

```bash
# 使用 pnpm
pnpm dev

# 或使用 npm
npm run dev

# 指定端口（如果 3000 被占用）
PORT=3001 pnpm dev
```

#### 4. 构建生产版本（可选）

```bash
# 构建
pnpm build

# 预览生产构建
pnpm start

# 或一步完成
pnpm build && pnpm start
```

---

## 🧪 验证安装

### 1. Backend 验证清单

```bash
# ✅ 健康检查
curl http://localhost:8000/health
# 预期: status = "ok"

# ✅ Business Date
curl http://localhost:8000/api/v1/dashboard/business-date
# 预期: business_date = "2026-07-12"

# ✅ KPI API
curl "http://localhost:8000/api/v1/dashboard/kpis?site=US&days=7"
# 预期: 返回包含 5 个 KPI 的 JSON

# ✅ Trends API
curl "http://localhost:8000/api/v1/dashboard/trends?site=DE&days=30"
# 预期: 返回包含 dates, gmv, asp, str_rate 的 JSON

# ✅ API 文档
open http://localhost:8000/docs
# 预期: 显示 Swagger UI
```

### 2. Frontend 验证清单

1. **访问 Dashboard** (http://localhost:3000)
   - [ ] 看到 "SignalPilot" 标题
   - [ ] 看到 3 个筛选器（Site, Category, Period）
   - [ ] 看到 5 个 KPI 卡片（GMV, SI, CTR, CVR, ASP）
   - [ ] 看到 3 张趋势图（GMV, ASP, STR）
   - [ ] 看到异常检测列表

2. **测试交互功能**
   - [ ] 切换 Site（US → DE → UK）
   - [ ] 选择 Category L1（Electronics）
   - [ ] 选择 Category L2（Phones）
   - [ ] 切换 Period（7 Days → 30 Days → Last Quarter）
   - [ ] 点击 Refresh 按钮
   - [ ] 所有操作后数据正常更新

3. **访问 AI Chat** (http://localhost:3000/chat)
   - [ ] 看到聊天界面
   - [ ] 输入测试问题（需要 API Key）
   - [ ] 收到 AI 回复

### 3. 数据验证

```bash
# 进入 data 目录
cd data

# 验证数据完整性
python validate_data_v2.py
```

**预期输出**:
```
============================================================
SignalPilot V2 数据验证器
============================================================

[1] 基础统计
  daily_metrics: 593,808 rows
  seller_daily_metrics: 4,156,656 rows
  inventory_daily: 593,808 rows
  campaigns: 47 rows
  sellers: 1,000 rows

[2] 日期范围
  Min date: 2024-01-01
  Max date: 2026-07-12
  Total days: 924

[3] 维度完整性
  Sites: 10 (US, DE, UK, AU, FR, IT, ES, CA, CN, JP)
  L1 Categories: 20
  L2 Categories: 81

[4] 数据质量
  GMV precision: 0.0048% avg error (acceptable)
  Top-down consistency: 100% (Seller GMV = Daily GMV)

✅ All checks passed!
```

---

## 🔍 常见问题与解决方案

### Backend 问题

#### Q1: `ModuleNotFoundError: No module named 'fastapi'`

**原因**: 依赖未安装或虚拟环境未激活

**解决**:
```bash
# 确保在虚拟环境中
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows

# 重新安装依赖
pip install fastapi uvicorn
```

#### Q2: `Cannot open file "signal.db": file not found`

**原因**: 数据库文件不存在

**解决**:
```bash
# 检查数据库位置
ls -la ../data/signal.db

# 如果不存在，重新生成
cd ../data
python generate_data_v2.py
cd ../backend
```

#### Q3: 端口 8000 已被占用

**错误信息**: `[Errno 48] Address already in use`

**解决**:
```bash
# 方法 1: 使用不同端口
uvicorn app.main:app --port 8001

# 方法 2: 停止占用进程
# Windows:
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# macOS/Linux:
lsof -ti:8000 | xargs kill -9
```

#### Q4: `database is locked`

**原因**: 多个进程同时访问数据库

**解决**:
```bash
# 1. 关闭所有访问数据库的进程
# 2. 重启 Backend
uvicorn app.main:app --reload
```

#### Q5: `ANTHROPIC_API_KEY not found`

**原因**: 环境变量未配置

**解决**:
```bash
# 创建 .env 文件
echo "ANTHROPIC_API_KEY=sk-ant-xxx" > backend/.env

# 或设置环境变量
export ANTHROPIC_API_KEY=sk-ant-xxx  # macOS/Linux
set ANTHROPIC_API_KEY=sk-ant-xxx    # Windows
```

---

### Frontend 问题

#### Q1: `pnpm install` 失败

**解决**:
```bash
# 清除缓存
pnpm store prune

# 删除 node_modules 和 lock 文件
rm -rf node_modules pnpm-lock.yaml

# 重新安装
pnpm install
```

#### Q2: 页面显示 "Failed to load data"

**检查清单**:
1. Backend 是否运行？访问 http://localhost:8000/health
2. `.env.local` 文件是否正确？应该包含 `NEXT_PUBLIC_API_URL=http://localhost:8000`
3. 浏览器控制台是否有 CORS 错误？

**解决**:
```bash
# 1. 确保 Backend 运行
cd backend
uvicorn app.main:app --reload

# 2. 检查环境变量
cat frontend/.env.local
# 应显示: NEXT_PUBLIC_API_URL=http://localhost:8000

# 3. 重启 Frontend
cd frontend
pnpm dev
```

#### Q3: 端口 3000 已被占用

**解决**:
```bash
# 方法 1: 使用不同端口
PORT=3001 pnpm dev

# 方法 2: 停止占用进程
# macOS/Linux:
lsof -ti:3000 | xargs kill -9

# Windows:
netstat -ano | findstr :3000
taskkill /F /PID <PID>
```

#### Q4: TypeScript 类型错误

**解决**:
```bash
# 重新安装类型定义
pnpm add -D @types/react @types/node

# 或跳过类型检查启动
pnpm dev -- --turbo
```

#### Q5: 样式不显示

**原因**: Tailwind CSS 未正确配置

**解决**:
```bash
# 检查 tailwind.config.js
cat tailwind.config.js

# 重新构建
rm -rf .next
pnpm dev
```

---

### 数据问题

#### Q1: 数据库文件不存在

**解决**:
```bash
cd data
python generate_data_v2.py
```

**预期输出**:
```
============================================================
SignalPilot V2 数据生成器
============================================================
[INFO] 创建表结构...
[OK] 表结构创建完成
[INFO] 生成 daily_metrics (593,808 rows)...
[OK] daily_metrics 完成
[INFO] 生成 seller_daily_metrics (4,156,656 rows)...
[OK] seller_daily_metrics 完成
...
[SUCCESS] 数据生成完成!
============================================================
```

#### Q2: 数据生成失败

**解决**:
```bash
# 1. 安装 duckdb
pip install duckdb

# 2. 删除旧数据库
rm data/signal.db

# 3. 重新生成
cd data
python generate_data_v2.py

# 4. 验证数据
python validate_data_v2.py
```

#### Q3: Business Date 不正确

**检查**:
```bash
# 查询 Business Date
curl http://localhost:8000/api/v1/dashboard/business-date

# 直接查询数据库
python -c "
import duckdb
conn = duckdb.connect('data/signal.db')
print('Max date:', conn.execute('SELECT MAX(date) FROM daily_metrics').fetchone()[0])
conn.close()
"
```

---

## 🎯 功能测试清单

完成安装后，测试以下功能：

### Dashboard 功能

**基础展示**:
- [ ] 访问 http://localhost:3000
- [ ] 看到 5 个 KPI 卡片（GMV, SI, CTR, CVR, ASP）
- [ ] KPI 显示数值和环比变化
- [ ] 看到 3 张趋势图（GMV, ASP, STR）
- [ ] 趋势图横向 3 列并排显示
- [ ] 看到异常检测列表

**筛选功能**:
- [ ] Site 筛选器：切换 US → DE → UK
- [ ] Category L1 筛选器：选择 "Electronics"
- [ ] Category L2 筛选器：选择 "Phones"（L1 选中后出现）
- [ ] Period 筛选器：切换 "Last 7 days" → "Last Quarter" → "2024 Full Year"
- [ ] 所有筛选后数据正确更新

**交互功能**:
- [ ] 点击 Refresh 按钮刷新数据
- [ ] 点击 "AI Agent" 按钮跳转到 Chat 页面
- [ ] 趋势图鼠标悬停显示详细数值
- [ ] 响应式布局（缩小浏览器窗口测试）

### AI Chat 功能（需要 API Key）

**基础功能**:
- [ ] 访问 http://localhost:3000/chat
- [ ] 看到聊天输入框
- [ ] 输入 "美国站过去 7 天的 GMV"
- [ ] 收到 AI 回复和数据表格
- [ ] SQL 查询包含正确的日期范围

**高级测试**:
- [ ] "按 L2 分类汇总 GMV"
- [ ] "库存健康度分析"
- [ ] "德国站 Electronics 的 ASP 趋势"
- [ ] 所有查询返回正确数据

### Backend API 测试

- [ ] 访问 http://localhost:8000/docs
- [ ] 看到 Swagger API 文档
- [ ] 测试 `/health` 端点
- [ ] 测试 `/api/v1/dashboard/business-date` 端点
- [ ] 测试 `/api/v1/dashboard/kpis` 端点
- [ ] 测试 `/api/v1/dashboard/trends` 端点
- [ ] 测试 `/api/v1/dashboard/anomalies` 端点
- [ ] 测试 `/api/v1/chat/query` 端点

---

## 📊 系统要求

### 最低要求
- **CPU**: 双核处理器（2 GHz+）
- **RAM**: 4 GB
- **硬盘**: 2 GB 可用空间
- **网络**: 互联网连接（安装依赖时需要）
- **操作系统**: Windows 10+, macOS 11+, Ubuntu 20.04+

### 推荐配置
- **CPU**: 四核处理器（3 GHz+）
- **RAM**: 8 GB 或更多
- **硬盘**: 5 GB 可用空间（包括 node_modules）
- **网络**: 稳定的互联网连接

---

## 🛠️ 开发工具推荐

### VS Code 扩展

**Python 开发**:
- Python (ms-python.python)
- Pylance (ms-python.vscode-pylance)
- Python Debugger (ms-python.debugpy)

**前端开发**:
- ESLint (dbaeumer.vscode-eslint)
- Prettier (esbenp.prettier-vscode)
- Tailwind CSS IntelliSense (bradlc.vscode-tailwindcss)
- TypeScript Vue Plugin (Volar) (Vue.vscode-typescript-vue-plugin)

**通用工具**:
- GitLens (eamodio.gitlens)
- REST Client (humao.rest-client)
- Better Comments (aaron-bond.better-comments)

### 浏览器推荐

- **Chrome** (推荐) - React DevTools, 最佳开发工具
- **Edge** (Chromium) - 与 Chrome 功能相同
- **Firefox** (支持) - 可能有轻微样式差异

---

## 🔄 维护和更新

### 更新依赖

**Backend**:
```bash
cd backend
pip install --upgrade -r requirements.txt
```

**Frontend**:
```bash
cd frontend
pnpm update
```

### 重新生成数据

```bash
cd data

# 删除旧数据库
rm signal.db

# 生成新数据
python generate_data_v2.py

# 验证数据
python validate_data_v2.py
```

### 清理和重置

```bash
# 停止所有服务器（Ctrl+C）

# 清理 Backend
cd backend
rm -rf __pycache__ .pytest_cache
find . -type d -name __pycache__ -exec rm -rf {} +

# 清理 Frontend
cd frontend
rm -rf node_modules .next pnpm-lock.yaml
pnpm install

# 清理数据库
rm data/signal.db
cd data && python generate_data_v2.py
```

---

## 🎓 下一步

安装成功后，你可以：

### 1. 探索功能
- 浏览 Dashboard，观察不同站点和分类的数据
- 测试 AI Chat，尝试各种自然语言查询
- 查看异常检测，了解业务波动

### 2. 学习代码
- `backend/app/api/dashboard_v2.py` - Dashboard API 实现
- `backend/app/agents/sql_agent.py` - SQL 生成 Agent
- `frontend/app/page.tsx` - Dashboard 页面
- `frontend/components/MultiTrendChart.tsx` - 趋势图组件

### 3. 阅读文档
- [README.md](../README.md) - 项目概览
- [docs/PRD.md](../docs/PRD.md) - 产品需求
- [docs/ARCHITECTURE.md](../docs/ARCHITECTURE.md) - 技术架构
- [STATUS.md](../STATUS.md) - 项目状态

### 4. 贡献代码
- Fork 本仓库
- 创建 feature 分支
- 提交 Pull Request

---

## 📞 获取帮助

### 遇到问题？

1. **查看日志**
   - Backend: 终端输出
   - Frontend: 浏览器控制台 (F12)

2. **检查文档**
   - 本文档的"常见问题"部分
   - [FastAPI 文档](https://fastapi.tiangolo.com/)
   - [Next.js 文档](https://nextjs.org/docs)

3. **搜索 Issues**
   - 查看 GitHub Issues
   - 搜索相似问题

4. **提交 Issue**
   - 描述问题和复现步骤
   - 附上错误日志
   - 注明操作系统和版本

---

## ✅ 安装成功标志

如果你看到以下内容，说明安装成功：

### Backend 终端
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
[info] application_starting version=1.0.0
[info] database_connected schema_version=v2
[info] max_date_fetched max_date=2026-07-12
```

### Frontend 终端
```
▲ Next.js 15.1.8 (Turbopack)
- Local:        http://localhost:3000
✓ Starting...
✓ Ready in 2.1s
```

### 浏览器界面
- ✅ SignalPilot Dashboard 正常显示
- ✅ 5 个 KPI 卡片有数据
- ✅ 3 张趋势图正常渲染
- ✅ 异常列表有内容
- ✅ 筛选器可以交互

---

**恭喜！🎉 你已成功运行 SignalPilot 项目！**

现在可以开始探索这个 AI 驱动的业务诊断平台了。

如果遇到任何问题，请参考"常见问题"部分或提交 Issue。

**Happy Coding! 🚀**
