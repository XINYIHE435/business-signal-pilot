"""
Chat API - AI 查询接口

提供 Phase 2 Orchestrator V2 的 HTTP API
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from app.agents.orchestrator_v2 import run_query
from app.tools import tool_registry
from app.tools.database_tool import DatabaseTool
from app.adapters.database import DuckDBAdapter
from app.core.config import settings

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])


# === Request/Response Models ===

class Message(BaseModel):
    """对话消息"""
    role: str  # "user" | "assistant"
    content: str
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Chat 请求"""
    query: str
    session_id: Optional[str] = "default"
    conversation_history: Optional[List[Message]] = []


class ChatResponse(BaseModel):
    """Chat 响应"""
    success: bool
    intent: str
    entities: Dict[str, Any]
    response: Dict[str, Any]
    reasoning_trace: List[Dict[str, Any]]
    tool_calls: List[Dict[str, Any]]
    timestamp: str


# === Startup: 注册 Database Tool ===

def initialize_tools():
    """初始化并注册工具"""
    try:
        from pathlib import Path

        # 获取项目根目录
        project_root = Path(__file__).parent.parent.parent.parent
        db_path = project_root / settings.database_path

        logger.info("initializing_tools", db_path=str(db_path))

        if not db_path.exists():
            logger.warning("database_file_not_found", path=str(db_path))
            # 不抛出异常，允许系统继续运行（SQL Agent 会处理）
            return

        # 创建 Database Adapter
        adapter = DuckDBAdapter(str(db_path), read_only=False)

        # 创建并注册 Database Tool
        db_tool = DatabaseTool(adapter)
        tool_registry.register(db_tool)

        logger.info("tools_initialized", tools=tool_registry.list_tools())

    except Exception as e:
        logger.error("tool_initialization_failed", error=str(e))
        # 不抛出异常，允许系统继续（SQL Agent 会自己创建工具）


# 在模块加载时初始化
initialize_tools()


# === API Endpoints ===

@router.post("/query", response_model=ChatResponse)
async def chat_query(request: ChatRequest):
    """
    处理用户查询

    使用 Orchestrator V2 进行意图分类、SQL 生成和执行

    Example:
        POST /api/v1/chat/query
        {
            "query": "查询德国站GMV",
            "session_id": "user123"
        }
    """
    try:
        logger.info(
            "chat_query_received",
            query=request.query[:50],
            session_id=request.session_id
        )

        # 转换对话历史格式
        history = [
            {"role": msg.role, "content": msg.content}
            for msg in request.conversation_history
        ]

        # 执行查询
        result = await run_query(
            query=request.query,
            session_id=request.session_id,
            conversation_history=history
        )

        # 构建响应
        response = ChatResponse(
            success=result["response"].get("success", True),
            intent=result["intent"],
            entities=result["entities"],
            response=result["response"],
            reasoning_trace=result["reasoning_trace"],
            tool_calls=result["tool_calls"],
            timestamp=datetime.now().isoformat()
        )

        logger.info(
            "chat_query_success",
            intent=result["intent"],
            response_type=result["response"]["type"]
        )

        return response

    except Exception as e:
        logger.error("chat_query_failed", error=str(e), query=request.query)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get("/health")
async def chat_health():
    """
    健康检查

    检查 Chat API 是否正常工作
    """
    return {
        "status": "ok",
        "tools_registered": tool_registry.list_tools(),
        "anthropic_configured": bool(settings.anthropic_api_key),
        "database_path": settings.database_path
    }


@router.get("/intents")
async def list_intents():
    """
    列出支持的意图类型
    """
    return {
        "intents": [
            {
                "name": "data_query",
                "description": "数据查询 - 简单的数据检索",
                "example": "查询德国站GMV"
            },
            {
                "name": "root_cause_analysis",
                "description": "根因分析 - 诊断业务问题",
                "example": "为什么德国站GMV下降了？"
            },
            {
                "name": "report_generation",
                "description": "报告生成 - 创建业务报告",
                "example": "生成本周业务报告"
            },
            {
                "name": "what_if_simulation",
                "description": "假设分析 - 模拟假设场景",
                "example": "如果预算增加10%会怎样？"
            },
            {
                "name": "comparison_analysis",
                "description": "对比分析 - 比较不同维度",
                "example": "对比德国站和英国站的表现"
            }
        ]
    }
