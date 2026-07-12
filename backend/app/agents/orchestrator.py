"""
Simple Orchestrator - 简单的 LangGraph Workflow

这是第一个版本，实现基本的意图分类 → SQL 执行 → 响应流程
"""

from typing import TypedDict, Annotated, List, Dict, Any
from datetime import datetime
import operator
import structlog

from langgraph.graph import StateGraph, END

logger = structlog.get_logger()


# === Agent State 定义 ===
class AgentState(TypedDict):
    """全局状态，在所有节点间流转"""

    # 输入
    user_query: str
    session_id: str

    # 意图理解
    intent: str  # "data_query" | "diagnosis" | "report"
    entities: Dict[str, Any]  # {"metric": "gmv", "site": "DE", ...}

    # Tool 调用记录（使用 operator.add 自动累加）
    tool_calls: Annotated[List[Dict], operator.add]
    tool_results: Annotated[List[Dict], operator.add]

    # 推理轨迹（用于 observability）
    reasoning_trace: Annotated[List[Dict], operator.add]

    # 输出
    final_response: Dict[str, Any]
    should_end: bool


# === Node 实现 ===

def simple_intent_node(state: AgentState) -> Dict:
    """
    简单的意图分类节点（暂不使用 LLM）

    根据关键词简单判断意图
    """
    query = state["user_query"].lower()

    # 简单的关键词匹配
    if any(word in query for word in ["why", "为什么", "下降", "上升", "异常", "问题"]):
        intent = "diagnosis"
    elif any(word in query for word in ["报告", "report", "周报", "月报"]):
        intent = "report"
    else:
        intent = "data_query"

    logger.info("intent_classified", query=query[:50], intent=intent)

    return {
        "intent": intent,
        "reasoning_trace": [{
            "node": "simple_intent",
            "timestamp": datetime.now().isoformat(),
            "intent": intent,
            "method": "keyword_matching"
        }]
    }


def simple_sql_node(state: AgentState) -> Dict:
    """
    简单的 SQL 节点（暂时返回 mock 数据）

    后续会替换为真正的 SQL Agent
    """
    query = state["user_query"]

    logger.info("sql_node_executed", query=query[:50])

    # Mock SQL 结果
    mock_result = {
        "sql": "SELECT SUM(gmv) FROM daily_metrics WHERE site='DE'",
        "data": [{"total_gmv": 1234567.89}],
        "explanation": "Querying total GMV for DE site"
    }

    return {
        "tool_calls": [{"tool": "execute_sql", "timestamp": datetime.now().isoformat()}],
        "tool_results": [mock_result],
        "reasoning_trace": [{
            "node": "simple_sql",
            "timestamp": datetime.now().isoformat(),
            "sql_generated": True
        }]
    }


def synthesizer_node(state: AgentState) -> Dict:
    """
    结果综合节点

    将所有中间结果组合成最终响应
    """
    intent = state["intent"]
    tool_results = state.get("tool_results", [])

    logger.info("synthesizing_response", intent=intent, result_count=len(tool_results))

    # 简单的响应格式化
    if intent == "data_query" and tool_results:
        response = {
            "type": "data_query",
            "data": tool_results[0].get("data", []),
            "sql": tool_results[0].get("sql", ""),
            "message": "查询完成"
        }
    elif intent == "diagnosis":
        response = {
            "type": "diagnosis",
            "message": "诊断功能即将上线"
        }
    else:
        response = {
            "type": "unknown",
            "message": "暂不支持此类查询"
        }

    return {
        "final_response": response,
        "should_end": True,
        "reasoning_trace": [{
            "node": "synthesizer",
            "timestamp": datetime.now().isoformat(),
            "response_type": response["type"]
        }]
    }


# === Workflow 构建 ===

def create_simple_workflow() -> StateGraph:
    """
    创建简单的 LangGraph Workflow

    流程: intent → sql → synthesizer → END
    """
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent", simple_intent_node)
    workflow.add_node("sql", simple_sql_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 设置入口
    workflow.set_entry_point("intent")

    # 简单的线性流程
    workflow.add_edge("intent", "sql")
    workflow.add_edge("sql", "synthesizer")
    workflow.add_edge("synthesizer", END)

    return workflow


def compile_workflow() -> Any:
    """
    编译 Workflow 为可执行的 app

    Returns:
        编译后的 LangGraph app
    """
    workflow = create_simple_workflow()
    app = workflow.compile()

    logger.info("workflow_compiled", nodes=["intent", "sql", "synthesizer"])

    return app


# === 便捷执行函数 ===

async def run_simple_query(query: str, session_id: str = "default") -> Dict[str, Any]:
    """
    执行简单查询

    Args:
        query: 用户查询
        session_id: 会话 ID

    Returns:
        最终响应
    """
    app = compile_workflow()

    # 初始状态
    initial_state = {
        "user_query": query,
        "session_id": session_id,
        "intent": "",
        "entities": {},
        "tool_calls": [],
        "tool_results": [],
        "reasoning_trace": [],
        "final_response": {},
        "should_end": False
    }

    # 执行 workflow
    final_state = await app.ainvoke(initial_state)

    return {
        "response": final_state["final_response"],
        "reasoning_trace": final_state["reasoning_trace"],
        "tool_calls": final_state["tool_calls"]
    }
