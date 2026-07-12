"""
Orchestrator V2 - 使用真正的 Intent Classifier 和 SQL Agent

集成 Phase 2 实现的 Agents
"""

from typing import TypedDict, Annotated, List, Dict, Any
from datetime import datetime
import operator
import structlog

from langgraph.graph import StateGraph, END
from app.agents.intent_classifier import intent_classifier_node
from app.agents.sql_agent import sql_agent_node

logger = structlog.get_logger()


# === Agent State 定义 ===
class AgentState(TypedDict):
    """全局状态，在所有节点间流转"""

    # 输入
    user_query: str
    session_id: str
    conversation_history: List[Dict]

    # 意图理解
    intent: str
    entities: Dict[str, Any]

    # Tool 调用记录
    tool_calls: Annotated[List[Dict], operator.add]
    tool_results: Annotated[List[Dict], operator.add]

    # 推理轨迹
    reasoning_trace: Annotated[List[Dict], operator.add]

    # 输出
    final_response: Dict[str, Any]
    should_end: bool


# === Synthesizer Node ===

def synthesizer_node(state: Dict) -> Dict:
    """
    结果综合节点 - 格式化最终响应
    """
    intent = state["intent"]
    tool_results = state.get("tool_results", [])
    entities = state.get("entities", {})

    logger.info("synthesizing_response", intent=intent, result_count=len(tool_results))

    # 根据意图格式化响应
    if intent == "data_query" and tool_results:
        # 数据查询结果
        sql_result = tool_results[0]

        if sql_result.get("success"):
            response = {
                "type": "data_query",
                "success": True,
                "data": sql_result.get("data", []),
                "sql": sql_result.get("sql", ""),
                "explanation": sql_result.get("explanation", ""),
                "row_count": sql_result.get("row_count", 0),
                "message": f"查询成功，返回 {sql_result.get('row_count', 0)} 行数据"
            }
        else:
            response = {
                "type": "data_query",
                "success": False,
                "error": sql_result.get("error", "Unknown error"),
                "message": "查询失败"
            }

    elif intent == "root_cause_analysis":
        # 根因分析（Phase 2 暂未实现）
        response = {
            "type": "diagnosis",
            "success": True,
            "message": "根因分析功能即将在 Phase 2 完成",
            "note": "需要实现 Diagnosis Agent"
        }

    elif intent == "report_generation":
        response = {
            "type": "report",
            "success": True,
            "message": "报告生成功能将在 Phase 2 实现"
        }

    elif intent == "comparison_analysis":
        response = {
            "type": "comparison",
            "success": True,
            "message": "对比分析功能将在 Phase 2 实现"
        }

    else:
        response = {
            "type": "unknown",
            "success": False,
            "message": f"暂不支持此类查询: {intent}"
        }

    return {
        "final_response": response,
        "should_end": True,
        "reasoning_trace": [{
            "node": "synthesizer",
            "timestamp": datetime.now().isoformat(),
            "response_type": response["type"],
            "success": response.get("success", False)
        }]
    }


# === Workflow 构建 ===

def create_orchestrator_v2() -> StateGraph:
    """
    创建 Orchestrator V2 Workflow

    流程: intent_classifier → sql_agent → synthesizer → END
    """
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("sql_agent", sql_agent_node)
    workflow.add_node("synthesizer", synthesizer_node)

    # 设置入口
    workflow.set_entry_point("intent_classifier")

    # 条件路由（根据意图）
    def route_by_intent(state: Dict) -> str:
        """根据意图决定下一步"""
        intent = state.get("intent", "data_query")

        if intent == "data_query":
            return "sql_agent"
        elif intent == "root_cause_analysis":
            # TODO: Phase 2 后期添加 diagnosis_agent
            return "synthesizer"
        else:
            return "synthesizer"

    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "sql_agent": "sql_agent",
            "synthesizer": "synthesizer"
        }
    )

    # 其他路径
    workflow.add_edge("sql_agent", "synthesizer")
    workflow.add_edge("synthesizer", END)

    logger.info("orchestrator_v2_created")

    return workflow


def compile_orchestrator_v2():
    """编译 Orchestrator V2"""
    workflow = create_orchestrator_v2()
    app = workflow.compile()

    logger.info("orchestrator_v2_compiled")

    return app


# === 便捷执行函数 ===

async def run_query(
    query: str,
    session_id: str = "default",
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    执行查询（使用 Orchestrator V2）

    Args:
        query: 用户查询
        session_id: 会话 ID
        conversation_history: 对话历史

    Returns:
        {
            "response": Dict,
            "reasoning_trace": List[Dict],
            "tool_calls": List[Dict],
            "intent": str,
            "entities": Dict
        }
    """
    app = compile_orchestrator_v2()

    # 初始状态
    initial_state = {
        "user_query": query,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "intent": "",
        "entities": {},
        "tool_calls": [],
        "tool_results": [],
        "reasoning_trace": [],
        "final_response": {},
        "should_end": False
    }

    # 执行 workflow
    logger.info("executing_orchestrator_v2", query=query[:50])

    try:
        final_state = await app.ainvoke(initial_state)

        return {
            "response": final_state["final_response"],
            "reasoning_trace": final_state["reasoning_trace"],
            "tool_calls": final_state["tool_calls"],
            "intent": final_state["intent"],
            "entities": final_state["entities"]
        }

    except Exception as e:
        logger.error("orchestrator_v2_failed", error=str(e))
        return {
            "response": {
                "type": "error",
                "success": False,
                "error": str(e),
                "message": "查询执行失败"
            },
            "reasoning_trace": [],
            "tool_calls": [],
            "intent": "unknown",
            "entities": {}
        }
