# 🚀 SignalPilot 快速启动指南

本指南将帮助你从零开始运行 SignalPilot 项目。

---

## 📋 前置要求

### 必需软件
- **Python 3.11+** ([下载](https://www.python.org/downloads/))
- **Node.js 18+** ([下载](https://nodejs.org/))
- **npm** (Node.js 自带) 或 **pnpm** (推荐)

### 可选软件
- **Git** (用于克隆项目)
- **VS Code** (推荐的代码编辑器)

### 验证安装
```bash
# 检查 Python 版本
python --version
# 应该显示: Python 3.11.x 或更高

# 检查 Node.js 版本
node --version
# 应该显示: v18.x.x 或更高

# 检查 npm 版本
npm --version
```

---

## 🎯 快速启动（5 分钟）

### Step 1: 获取项目代码

```bash
# 如果使用 Git
git clone https://github.com/yourusername/business-signal-pilot.git
cd business-signal-pilot

# 或者直接解压下载的 ZIP 文件
cd business-signal-pilot
```

### Step 2: 启动 Backend（终端 1）

```bash
# 进入 backend 目录
cd backend

# 安装 Python 依赖
pip install fastapi uvicorn structlog python-multipart httpx pytest pytest-asyncio anthropic openai pydantic-settings duckdb

# 启动 Backend 服务器
python -m app.main
```

**预期输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
{"event": "application_starting", "version": "1.0.0", ...}
{"event": "database_connected", ...}
```

**验证：**
- 打开浏览器访问 http://localhost:8000/docs
- 应该看到 Swagger API 文档界面

### Step 3: 启动 Frontend（终端 2）

打开**新的终端窗口**，执行：

```bash
# 进入 frontend 目录
cd frontend

# 安装 Node.js 依赖
npm install

# 启动 Frontend 服务器
npm run dev
```

**预期输出：**
```
▲ Next.js 16.2.9 (Turbopack)
- Local:   http://localhost:3000
✓ Ready in 1893ms
```

**验证：**
- 打开浏览器访问 http://localhost:3000
- 应该看到 SignalPilot Dashboard 界面

### Step 4: 访问应用

**Frontend (用户界面):**
- 地址：http://localhost:3000
- 功能：Dashboard、KPI 卡片、趋势图、异常检测

**Backend (API 服务):**
- 地址：http://localhost:8000
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

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
```

#### 2. 安装依赖

```bash
pip install -r requirements.txt
```

如果 `requirements.txt` 安装失败，使用以下命令单独安装：

```bash
pip install fastapi==0.138.0 uvicorn==0.49.0 structlog==26.1.0 python-multipart==0.0.32 httpx pytest pytest-asyncio anthropic openai pydantic-settings
```

#### 3. 配置环境变量（可选）

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件（可选，AI 功能需要）
# ANTHROPIC_API_KEY=your_key_here
# OPENAI_API_KEY=your_key_here
```

**注意：** 基础功能（Dashboard）不需要 AI API Key。

#### 4. 验证数据库

```bash
# 检查数据库文件是否存在
python -c "import os; print('Database exists:', os.path.exists('../data/signal.db'))"
```

如果数据库不存在，运行：

```bash
cd ../data
python generate_data.py
cd ../backend
```

#### 5. 启动服务器

```bash
python -m app.main
```

或使用 uvicorn：

```bash
uvicorn app.main:app --reload
```

**测试 API：**
```bash
# 健康检查
curl http://localhost:8000/health

# 获取 KPI
curl "http://localhost:8000/api/v1/dashboard/kpis?site=DE"
```

---

### Frontend 详细步骤

#### 1. 安装依赖

```bash
cd frontend

# 使用 npm
npm install

# 或使用 pnpm（更快）
pnpm install
```

#### 2. 配置环境变量

```bash
# 创建 .env.local 文件
echo "NEXT_PUBLIC_API_URL=http://localhost:8000" > .env.local
```

或手动创建 `.env.local` 文件，内容：
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### 3. 启动开发服务器

```bash
npm run dev
```

#### 4. 构建生产版本（可选）

```bash
npm run build
npm start
```

---

## 🧪 验证安装

### 1. Backend 验证

```bash
# 测试健康检查
curl http://localhost:8000/health

# 预期响应：
# {
#   "status": "ok",
#   "database_connected": true,
#   "llm_available": false,
#   "version": "1.0.0"
# }

# 测试 KPI API
curl "http://localhost:8000/api/v1/dashboard/kpis?site=DE&days=7"

# 预期响应：包含 5 个 KPI 的 JSON 数据
```

### 2. Frontend 验证

1. 打开浏览器访问 http://localhost:3000
2. 应该看到：
   - ✅ SignalPilot 标题
   - ✅ Site 和 Period 筛选器
   - ✅ 5 个 KPI 卡片（GMV, SI, CTR, CVR, ASP）
   - ✅ GMV 趋势图
   - ✅ 异常检测列表

3. 测试交互：
   - 切换不同的 Site（US, DE, UK...）
   - 切换不同的 Period（7天、14天、30天）
   - 点击 Refresh 按钮

---

## 🔍 常见问题

### Backend 问题

#### Q1: `ModuleNotFoundError: No module named 'fastapi'`
**解决：**
```bash
pip install fastapi uvicorn
```

#### Q2: `Cannot open file "signal.db": file not found`
**解决：**
```bash
cd data
python generate_data.py
cd ../backend
```

#### Q3: 端口 8000 已被占用
**解决：**
```bash
# 方法 1: 使用不同端口
uvicorn app.main:app --port 8001

# 方法 2: 停止占用 8000 的进程
# Windows:
netstat -ano | findstr :8000
taskkill /F /PID <PID>

# macOS/Linux:
lsof -ti:8000 | xargs kill
```

#### Q4: `database is locked`
**解决：**
```bash
# 关闭其他正在使用数据库的进程
# 或者重启 Backend 服务器
```

---

### Frontend 问题

#### Q1: `npm install` 失败
**解决：**
```bash
# 清除缓存
npm cache clean --force

# 删除 node_modules
rm -rf node_modules package-lock.json

# 重新安装
npm install
```

#### Q2: 页面显示 "Failed to load data"
**检查：**
1. Backend 服务器是否运行（http://localhost:8000/health）
2. `.env.local` 文件是否正确配置
3. 浏览器控制台是否有 CORS 错误

**解决：**
```bash
# 确保 Backend 已启动
cd backend
python -m app.main

# 确保环境变量正确
cat frontend/.env.local
# 应该显示: NEXT_PUBLIC_API_URL=http://localhost:8000
```

#### Q3: 端口 3000 已被占用
**解决：**
```bash
# 使用不同端口
PORT=3001 npm run dev
```

#### Q4: TypeScript 编译错误
**解决：**
```bash
# 重新安装依赖
npm install lucide-react recharts swr

# 或跳过类型检查启动
npm run dev -- --no-type-check
```

---

### 数据问题

#### Q1: 数据库文件不存在
**解决：**
```bash
cd data
python generate_data.py
```

预期输出：
```
============================================================
SignalPilot 数据生成器
============================================================
[INFO] 创建表结构...
[OK] 表结构创建完成
[INFO] 生成 daily_metrics 数据...
...
[SUCCESS] 数据生成完成!
```

#### Q2: 数据生成失败
**解决：**
```bash
# 安装 duckdb
pip install duckdb

# 删除旧数据库
rm data/signal.db

# 重新生成
cd data
python generate_data.py
```

---

## 🎯 功能测试清单

完成安装后，测试以下功能：

### Dashboard 功能
- [ ] 访问 http://localhost:3000
- [ ] 看到 5 个 KPI 卡片
- [ ] KPI 显示数值和变化百分比
- [ ] 看到 GMV 趋势图
- [ ] 趋势图显示最近 30 天数据
- [ ] 看到异常检测列表
- [ ] 切换不同 Site（US, DE, UK...）
- [ ] 切换不同 Period（7天、14天、30天）
- [ ] 点击 Refresh 按钮刷新数据

### Backend API 测试
- [ ] 访问 http://localhost:8000/docs
- [ ] 看到 Swagger API 文档
- [ ] 测试 `/health` 端点
- [ ] 测试 `/api/v1/dashboard/kpis` 端点
- [ ] 测试 `/api/v1/dashboard/trends` 端点
- [ ] 测试 `/api/v1/dashboard/anomalies` 端点

---

## 📊 系统要求

### 最低要求
- **CPU:** 双核处理器
- **RAM:** 4GB
- **硬盘:** 2GB 可用空间
- **网络:** 互联网连接（用于安装依赖）

### 推荐配置
- **CPU:** 四核处理器
- **RAM:** 8GB 或更多
- **硬盘:** 5GB 可用空间
- **网络:** 稳定的互联网连接

---

## 🛠️ 开发工具

### 推荐的 VS Code 扩展
- **Python** (ms-python.python)
- **Pylance** (ms-python.vscode-pylance)
- **ESLint** (dbaeumer.vscode-eslint)
- **Prettier** (esbenp.prettier-vscode)
- **Tailwind CSS IntelliSense** (bradlc.vscode-tailwindcss)

### 推荐的浏览器
- **Chrome** (推荐，最佳开发工具)
- **Edge** (Chromium 内核)
- **Firefox** (支持，但可能有样式差异)

---

## 🔄 更新和维护

### 更新依赖

**Backend:**
```bash
cd backend
pip install --upgrade -r requirements.txt
```

**Frontend:**
```bash
cd frontend
npm update
```

### 重新生成数据

```bash
cd data
python generate_data.py
```

### 清理和重置

```bash
# 停止所有服务器
# Ctrl+C 在两个终端

# 删除数据库
rm data/signal.db

# 重新生成数据
cd data
python generate_data.py

# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +

# 清理 Node.js
cd frontend
rm -rf node_modules .next
npm install
```

---

## 🎓 下一步

安装成功后，你可以：

1. **探索 Dashboard**
   - 切换不同站点查看数据
   - 观察 KPI 变化趋势
   - 查看检测到的异常

2. **学习 API**
   - 访问 http://localhost:8000/docs
   - 尝试不同的 API 端点
   - 理解数据结构

3. **查看代码**
   - `backend/app/api/dashboard.py` - API 实现
   - `frontend/app/page.tsx` - Dashboard 页面
   - `frontend/components/` - React 组件

4. **阅读文档**
   - `docs/PRD.md` - 产品需求
   - `docs/ARCHITECTURE.md` - 技术架构
   - `docs/DEVELOPMENT_PLAN.md` - 开发计划

---

## 📞 获取帮助

如果遇到问题：

1. **查看日志**
   - Backend: 终端输出
   - Frontend: 浏览器控制台 (F12)

2. **检查文档**
   - [FastAPI 文档](https://fastapi.tiangolo.com/)
   - [Next.js 文档](https://nextjs.org/docs)
   - [项目文档](docs/)

3. **常见问题**
   - 查看本文档的"常见问题"部分
   - 查看 `STATUS.md` 了解项目状态

---

## ✅ 安装成功标志

如果你看到以下内容，说明安装成功：

✅ **Backend 终端显示：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
{"event": "database_connected", ...}
```

✅ **Frontend 终端显示：**
```
▲ Next.js 16.2.9
- Local:   http://localhost:3000
✓ Ready in 1893ms
```

✅ **浏览器显示：**
- SignalPilot Dashboard 界面
- 5 个 KPI 卡片有数据
- 趋势图正常显示
- 异常列表有内容

---

**恭喜！🎉 你已成功运行 SignalPilot 项目！**

现在可以开始探索和使用这个 AI 驱动的业务诊断平台了。
