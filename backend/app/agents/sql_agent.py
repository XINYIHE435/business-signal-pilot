"""
SQL Agent - Text-to-SQL Agent

使用 RAG 检索相关 Schema，然后生成和执行 SQL
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog

from anthropic import AsyncAnthropic
from app.core.config import settings
from app.tools.database_tool import DatabaseTool

logger = structlog.get_logger()


class SQLAgent:
    """SQL 生成和执行 Agent"""

    def __init__(self, database_tool: DatabaseTool):
        """
        初始化 SQL Agent

        Args:
            database_tool: Database Tool 实例
        """
        self.database_tool = database_tool

        if not settings.anthropic_api_key:
            logger.warning("anthropic_api_key_not_configured")
            self.client = None
        else:
            self.client = AsyncAnthropic(
                api_key=settings.anthropic_api_key,
                base_url=settings.ANTHROPIC_BASE_URL
            )
            logger.info("claude_client_initialized", base_url=settings.ANTHROPIC_BASE_URL)

    async def _retrieve_schema(self, query: str) -> str:
        """
        从 RAG 检索相关 Schema

        TODO: Phase 3 实现真正的 RAG
        现在返回硬编码的 Schema
        """
        # 目前返回所有表的 Schema
        schema_text = """
### Database Schema

#### Table: daily_metrics
Description: Daily business metrics aggregated by site and category

Columns:
- date (DATE): Date of the metrics
- site (VARCHAR): Site code (US, DE, UK, AU, FR, IT, ES, CA, CN, JP)
- category (VARCHAR): Product category (Electronics, Fashion, Home, etc.)
- gmv (DECIMAL): Gross Merchandise Value - total transaction amount
- sold_items (INTEGER): Number of items sold (SI)
- impressions (INTEGER): Number of impressions
- clicks (INTEGER): Number of clicks
- orders (INTEGER): Number of orders
- ctr (DECIMAL): Click-Through Rate (clicks/impressions)
- cvr (DECIMAL): Conversion Rate (orders/clicks)
- asp (DECIMAL): Average Selling Price (gmv/sold_items)
- active_sellers (INTEGER): Number of active sellers
- new_listings (INTEGER): Number of new listings

Indexes: date, site, category
Primary Key: (date, site, category)

Example Query:
```sql
SELECT date, SUM(gmv) as total_gmv
FROM daily_metrics
WHERE site = 'DE' AND date >= '2024-01-01'
GROUP BY date
ORDER BY date;
```

#### Table: campaigns
Description: Marketing campaigns

Columns:
- campaign_id (VARCHAR): Unique campaign ID
- campaign_name (VARCHAR): Campaign name
- site (VARCHAR): Site code
- category (VARCHAR): Target category (NULL = all categories)
- start_date (DATE): Campaign start date
- end_date (DATE): Campaign end date
- discount_rate (DECIMAL): Discount rate (0.15 = 15% off)
- subsidy_budget (DECIMAL): Total subsidy budget
- target_gmv (DECIMAL): Target GMV
- actual_gmv (DECIMAL): Actual GMV achieved
- roi (DECIMAL): Return on Investment

#### Table: sellers
Description: Seller information

Columns:
- seller_id (VARCHAR): Unique seller ID
- seller_name (VARCHAR): Seller name
- site (VARCHAR): Primary site
- country (VARCHAR): Seller location
- join_date (DATE): Registration date
- feedback_score (INTEGER): Feedback score
- is_top_rated (BOOLEAN): Top-rated seller flag
- status (VARCHAR): Status (active, suspended, churned)
- last_listing_date (DATE): Last listing date

### DuckDB SQL Guidelines
- Use DuckDB syntax (similar to PostgreSQL)
- Always use date filters for performance
- Use appropriate aggregations (SUM, AVG, COUNT)
- Avoid SELECT * on large tables
- Use LIMIT for large result sets
"""
        return schema_text

    async def generate_and_execute_sql(
        self,
        query: str,
        entities: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        生成 SQL 并执行

        Args:
            query: 用户查询
            entities: 提取的实体

        Returns:
            {
                "success": bool,
                "sql": str,
                "explanation": str,
                "data": List[Dict],
                "row_count": int
            }
        """
        if not self.client:
            logger.error("claude_client_not_available")
            return {
                "success": False,
                "error": "Claude client not configured"
            }

        # Step 1: 检索 Schema
        schema_context = await self._retrieve_schema(query)

        # Step 2: 准备 System Prompt
        system_prompt = f"""You are a SQL expert for business analytics on DuckDB.

{schema_context}

Your task:
1. Generate a SQL query based on the user's question
2. Provide a clear explanation of what the query does
3. Use the extracted entities to filter data appropriately

Guidelines:
- Always include date filters for performance
- Use meaningful column aliases
- Format numbers appropriately
- Keep queries efficient and focused
"""

        # Step 3: 准备 User Message
        user_message = f"""User Query: {query}

Extracted Entities:
{entities}

Generate a SQL query to answer this question."""

        # Step 4: 定义 Tool
        tools = [
            {
                "name": "execute_sql",
                "description": "Execute SQL query on DuckDB and return results",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sql": {
                            "type": "string",
                            "description": "SQL query to execute (DuckDB syntax)"
                        },
                        "explanation": {
                            "type": "string",
                            "description": "Brief explanation of what this query does"
                        }
                    },
                    "required": ["sql", "explanation"]
                }
            }
        ]

        try:
            # Step 5: 调用 Claude 生成 SQL
            response = await self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=2048,
                temperature=0.0,
                system=system_prompt,
                tools=tools,
                messages=[{"role": "user", "content": user_message}]
            )

            # Step 6: 提取 Tool Call
            tool_use_block = None
            for block in response.content:
                if block.type == "tool_use" and block.name == "execute_sql":
                    tool_use_block = block
                    break

            if not tool_use_block:
                logger.warning("no_sql_generated")
                return {
                    "success": False,
                    "error": "No SQL generated by LLM"
                }

            sql = tool_use_block.input["sql"]
            explanation = tool_use_block.input["explanation"]

            logger.info("sql_generated", sql=sql[:100], explanation=explanation[:100])

            # Step 7: 执行 SQL
            result = await self.database_tool.execute(
                sql=sql,
                explanation=explanation,
                max_rows=1000
            )

            logger.info(
                "sql_executed",
                success=result["success"],
                row_count=result.get("row_count", 0)
            )

            return result

        except Exception as e:
            logger.error("sql_agent_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }


# === LangGraph Node Wrapper ===

def sql_agent_node(state: Dict) -> Dict:
    """
    SQL Agent Node for LangGraph

    Args:
        state: AgentState

    Returns:
        State updates
    """
    import asyncio
    from pathlib import Path

    query = state["user_query"]
    entities = state.get("entities", {})

    try:
        # 直接创建 Database Adapter 和 Tool（不依赖 registry）
        from app.adapters.database import DuckDBAdapter
        from app.tools.database_tool import DatabaseTool
        from app.core.config import settings

        # 构建数据库路径
        project_root = Path(__file__).parent.parent.parent.parent
        db_path = project_root / settings.database_path

        if not db_path.exists():
            logger.error("database_file_not_found", path=str(db_path))
            return {
                "tool_calls": [{
                    "tool": "execute_sql",
                    "timestamp": datetime.now().isoformat(),
                    "success": False
                }],
                "tool_results": [{
                    "success": False,
                    "error": f"Database file not found: {db_path}"
                }],
                "reasoning_trace": [{
                    "node": "sql_agent",
                    "timestamp": datetime.now().isoformat(),
                    "error": "Database file not found"
                }]
            }

        # 创建 Adapter 和 Tool
        adapter = DuckDBAdapter(str(db_path), read_only=True)
        db_tool = DatabaseTool(adapter)

        # 创建 SQL Agent
        sql_agent = SQLAgent(db_tool)

        # 执行 SQL 生成和查询
        result = asyncio.run(sql_agent.generate_and_execute_sql(query, entities))

        return {
            "tool_calls": [{
                "tool": "execute_sql",
                "timestamp": datetime.now().isoformat(),
                "success": result["success"]
            }],
            "tool_results": [result],
            "reasoning_trace": [{
                "node": "sql_agent",
                "timestamp": datetime.now().isoformat(),
                "sql": result.get("sql", ""),
                "row_count": result.get("row_count", 0),
                "success": result["success"]
            }]
        }

    except Exception as e:
        logger.error("sql_agent_node_failed", error=str(e))
        return {
            "tool_calls": [{
                "tool": "execute_sql",
                "timestamp": datetime.now().isoformat(),
                "success": False
            }],
            "tool_results": [{
                "success": False,
                "error": str(e)
            }],
            "reasoning_trace": [{
                "node": "sql_agent",
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "success": False
            }]
        }
