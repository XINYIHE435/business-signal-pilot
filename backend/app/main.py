"""
SignalPilot FastAPI 应用入口

AI-Powered Cross-border Business Signal Diagnosis Platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog
import time
from datetime import datetime

from app.core.config import settings
from app.core.database_v2 import db_v2 as db
from app.core.llm import llm_client
from app.models.schemas import HealthResponse, ErrorResponse

# 配置结构化日志
structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.JSONRenderer()
    ]
)

logger = structlog.get_logger()

# 创建 FastAPI 应用
app = FastAPI(
    title="SignalPilot API",
    description="AI-Powered Cross-border Business Signal Diagnosis Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins + ["https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录所有请求"""
    start_time = time.time()

    # 处理请求
    response = await call_next(request)

    # 计算处理时间
    process_time = (time.time() - start_time) * 1000

    logger.info(
        "request_processed",
        method=request.method,
        path=request.url.path,
        status_code=response.status_code,
        process_time_ms=round(process_time, 2)
    )

    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(
        "unhandled_exception",
        path=request.url.path,
        error=str(exc),
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            error="Internal Server Error",
            detail=str(exc) if settings.debug else "An unexpected error occurred",
            timestamp=datetime.now()
        ).dict()
    )


# ============================================================
# 基础路由
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "message": "SignalPilot API",
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """健康检查"""

    # 检查数据库连接
    database_connected = False
    try:
        db.execute("SELECT 1")
        database_connected = True
    except Exception as e:
        logger.error("database_health_check_failed", error=str(e))

    # 检查 LLM 可用性
    llm_available = (
        llm_client.claude_client is not None or
        llm_client.openai_client is not None
    )

    return HealthResponse(
        status="ok" if database_connected else "degraded",
        database_connected=database_connected,
        llm_available=llm_available,
        version=settings.app_version
    )


# ============================================================
# API 路由
# ============================================================

from app.api.dashboard_v2 import router as dashboard_v2_router
from app.api.chat import router as chat_router
from app.api.diagnosis import router as diagnosis_router

# 注册 Dashboard 路由
app.include_router(dashboard_v2_router)

# 注册 Chat 路由（Phase 2）
app.include_router(chat_router)

# 注册 Diagnosis 路由（Phase 3）
app.include_router(diagnosis_router)

# 待添加的路由：
# - /api/v1/report/*


# ============================================================
# 启动和关闭事件
# ============================================================

@app.on_event("startup")
async def startup_event():
    """应用启动"""
    logger.info("application_starting", version=settings.app_version)

    # 测试数据库连接
    try:
        db.connect()
        logger.info("database_connection_established")
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))

    # 检查 LLM 配置
    if not settings.anthropic_api_key and not settings.openai_api_key:
        logger.warning("no_llm_api_keys_configured")
    else:
        logger.info("llm_client_ready", default_llm=settings.default_llm)


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭"""
    logger.info("application_shutting_down")

    # 关闭数据库连接
    try:
        db.close()
        logger.info("database_connection_closed")
    except Exception as e:
        logger.error("database_close_failed", error=str(e))


# ============================================================
# 运行应用（开发模式）
# ============================================================

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True,
        log_level=settings.log_level.lower()
    )
