"""
Intent Classifier Agent - 意图分类 Agent

使用 Claude Tool Calling 进行结构化的意图理解和实体提取
"""

from typing import Dict, Any
from datetime import datetime
import structlog

from anthropic import AsyncAnthropic
from app.core.config import settings

logger = structlog.get_logger()


class IntentClassifierAgent:
    """意图分类 Agent"""

    def __init__(self):
        """初始化 Intent Classifier"""
        if not settings.anthropic_api_key:
            logger.warning("anthropic_api_key_not_configured")
            self.client = None
        else:
            self.client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.ANTHROPIC_BASE_URL
            )
            logger.info("claude_client_initialized", base_url=settings.ANTHROPIC_BASE_URL)

    def _get_intent_tool_schema(self) -> Dict[str, Any]:
        """返回意图分类的 Tool Schema"""
        return {
            "name": "classify_intent",
            "description": "Classify user intent for business analytics query and extract entities",
            "input_schema": {
                "type": "object",
                "properties": {
                    "intent": {
                        "type": "string",
                        "enum": [
                            "data_query",
                            "root_cause_analysis",
                            "report_generation",
                            "what_if_simulation",
                            "comparison_analysis"
                        ],
                        "description": "Primary user intent"
                    },
                    "entities": {
                        "type": "object",
                        "properties": {
                            "metric": {
                                "type": "string",
                                "description": "Metric name (gmv, ctr, cvr, si, asp, etc.)"
                            },
                            "site": {
                                "type": "string",
                                "description": "Site code (US, DE, UK, etc.)"
                            },
                            "category": {
                                "type": "string",
                                "description": "Product category"
                            },
                            "date_range": {
                                "type": "string",
                                "description": "Date range (e.g., 'last 7 days', '2024-01-01 to 2024-01-31')"
                            },
                            "comparison": {
                                "type": "string",
                                "description": "Comparison type (e.g., 'WoW', 'YoY', 'vs DE')"
                            },
                            "threshold": {
                                "type": "number",
                                "description": "Threshold for anomaly detection"
                            }
                        },
                        "description": "Extracted entities from query"
                    },
                    "confidence": {
                        "type": "number",
                        "minimum": 0,
                        "maximum": 1,
                        "description": "Confidence score of classification"
                    },
                    "reasoning": {
                        "type": "string",
                        "description": "Brief explanation of classification"
                    }
                },
                "required": ["intent", "entities", "confidence", "reasoning"]
            }
        }

    async def classify(self, query: str, conversation_history: list = None) -> Dict[str, Any]:
        """
        分类用户意图并提取实体

        Args:
            query: 用户查询
            conversation_history: 对话历史（可选）

        Returns:
            {
                "intent": str,
                "entities": dict,
                "confidence": float,
                "reasoning": str
            }
        """
        if not self.client:
            logger.error("claude_client_not_available")
            return self._fallback_classification(query)

        # 构建上下文
        context = ""
        if conversation_history:
            recent_history = conversation_history[-3:]  # 最近 3 轮对话
            context = "\n".join([
                f"{msg['role']}: {msg['content']}"
                for msg in recent_history
            ])

        # System prompt
        system_prompt = """You are an expert in business analytics intent classification.

Your task is to:
1. Classify the user's intent into one of the predefined categories
2. Extract relevant entities (metrics, sites, date ranges, etc.)
3. Provide a confidence score

Business Context:
- This is an eBay cross-border business analytics platform
- Users are business analysts asking questions about GMV, traffic, conversion, etc.
- Common metrics: GMV (Gross Merchandise Value), SI (Sold Items), CTR (Click-Through Rate), CVR (Conversion Rate), ASP (Average Selling Price)
- Sites: US, DE (Germany), UK, AU, FR, IT, ES, CA, CN, JP

Intent Categories:
- data_query: Simple data retrieval (e.g., "Show me GMV for DE site")
- root_cause_analysis: Diagnosing issues (e.g., "Why did GMV drop?")
- report_generation: Creating reports (e.g., "Generate weekly report")
- what_if_simulation: Hypothetical scenarios (e.g., "What if we increase budget by 10%?")
- comparison_analysis: Comparing metrics (e.g., "Compare DE vs UK performance")

Be precise and extract all relevant entities."""

        user_message = query
        if context:
            user_message = f"Context:\n{context}\n\nCurrent Query:\n{query}"

        try:
            # 调用 Claude
            response = await self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=1024,
                temperature=0.0,  # 确定性输出
                system=system_prompt,
                tools=[self._get_intent_tool_schema()],
                messages=[{"role": "user", "content": user_message}]
            )

            # 提取 tool call 结果
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "classify_intent":
                    tool_use_block = block
                    break

            if not tool_use_block:
                logger.warning("no_tool_use_in_response")
                return self._fallback_classification(query)

            result = tool_use_block.input

            logger.info(
                "intent_classified",
                query=query[:50],
                intent=result["intent"],
                confidence=result["confidence"]
            )

            return {
                "intent": result["intent"],
                "entities": result["entities"],
                "confidence": result["confidence"],
                "reasoning": result["reasoning"]
            }

        except Exception as e:
            logger.error("intent_classification_failed", error=str(e), error_type=type(e).__name__)
            # 如果是网络错误，提供更详细的信息
            if "Connection" in str(e) or "timeout" in str(e).lower():
                logger.warning("api_connection_failed", suggestion="Check API key and network connectivity")
            return self._fallback_classification(query)

    def _fallback_classification(self, query: str) -> Dict[str, Any]:
        """
        备用分类方法（基于关键词）

        Args:
            query: 用户查询

        Returns:
            分类结果
        """
        query_lower = query.lower()

        # 简单关键词匹配
        if any(word in query_lower for word in ["why", "为什么", "下降", "drop", "上升", "increase", "异常", "issue"]):
            intent = "root_cause_analysis"
        elif any(word in query_lower for word in ["报告", "report", "周报", "weekly", "月报", "monthly"]):
            intent = "report_generation"
        elif any(word in query_lower for word in ["if", "假设", "what if", "simulation"]):
            intent = "what_if_simulation"
        elif any(word in query_lower for word in ["compare", "对比", "vs", "versus"]):
            intent = "comparison_analysis"
        else:
            intent = "data_query"

        logger.info("fallback_classification", query=query[:50], intent=intent)

        return {
            "intent": intent,
            "entities": {},
            "confidence": 0.5,
            "reasoning": "Fallback keyword-based classification"
        }


# 创建全局实例
intent_classifier = IntentClassifierAgent()


# === LangGraph Node Wrapper ===

def intent_classifier_node(state: Dict) -> Dict:
    """
    Intent Classifier Node for LangGraph

    Args:
        state: AgentState

    Returns:
        State updates
    """
    import asyncio

    query = state["user_query"]
    history = state.get("conversation_history", [])

    # 执行分类
    result = asyncio.run(intent_classifier.classify(query, history))

    return {
        "intent": result["intent"],
        "entities": result["entities"],
        "reasoning_trace": [{
            "node": "intent_classifier",
            "timestamp": datetime.now().isoformat(),
            "intent": result["intent"],
            "confidence": result["confidence"],
            "reasoning": result["reasoning"],
            "entities": result["entities"]
        }]
    }
