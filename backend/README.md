# Backend 项目说明

这是 SignalPilot 的 FastAPI 后端。

## 目录结构

```
app/
├── main.py              # FastAPI 应用入口
├── api/                 # API 路由
│   ├── dashboard.py     # Dashboard API
│   ├── diagnosis.py     # 诊断 API
│   ├── chat.py         # Chat API
│   └── report.py       # 报告 API
├── agents/             # AI Agents
│   ├── orchestrator.py # 调度中心
│   ├── sql_agent.py    # SQL 生成
│   └── diagnosis_agent.py # 诊断分析
├── core/               # 核心模块
│   ├── config.py       # 配置管理
│   ├── database.py     # 数据库连接
│   └── llm.py         # LLM 客户端
├── models/            # 数据模型
│   └── schemas.py     # Pydantic schemas
└── utils/             # 工具函数
    ├── anomaly_detection.py
    └── contribution_analysis.py
```

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
uvicorn app.main:app --reload
```

访问 API 文档: http://localhost:8000/docs
