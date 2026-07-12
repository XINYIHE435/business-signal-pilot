"""
Database Tool - SQL 执行工具

通过 Database Adapter 执行 SQL，支持多种数据库后端
"""

from typing import Any, Dict
import structlog

from app.tools.registry import BaseTool
from app.adapters.database.base import DatabaseAdapter

logger = structlog.get_logger()


class DatabaseTool(BaseTool):
    """数据库查询工具"""

    name = "execute_sql"
    description = "Execute SQL query on the data warehouse and return results"

    def __init__(self, adapter: DatabaseAdapter):
        """
        初始化 Database Tool

        Args:
            adapter: 数据库适配器实例
        """
        self.adapter = adapter

    def get_schema(self) -> Dict[str, Any]:
        """返回 LLM Function Calling Schema"""
        return {
            "name": self.name,
            "description": self.description,
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
                    },
                    "max_rows": {
                        "type": "integer",
                        "description": "Maximum number of rows to return",
                        "default": 1000
                    }
                },
                "required": ["sql", "explanation"]
            }
        }

    async def execute(self, sql: str, explanation: str = "", max_rows: int = 1000, **kwargs) -> Dict[str, Any]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            explanation: 查询说明
            max_rows: 最大返回行数
            **kwargs: 其他参数（忽略）

        Returns:
            {
                "success": bool,
                "data": List[Dict],
                "row_count": int,
                "truncated": bool,
                "sql": str,
                "explanation": str
            }
        """
        logger.info("database_tool_execute", sql=sql[:100], max_rows=max_rows)

        try:
            # 执行 SQL
            results = await self.adapter.execute(sql)

            truncated = len(results) > max_rows
            data = results[:max_rows]

            response = {
                "success": True,
                "data": data,
                "row_count": len(results),
                "returned_rows": len(data),
                "truncated": truncated,
                "sql": sql,
                "explanation": explanation
            }

            logger.info(
                "database_tool_success",
                row_count=len(results),
                returned_rows=len(data),
                truncated=truncated
            )

            return response

        except Exception as e:
            logger.error("database_tool_failed", sql=sql[:100], error=str(e))

            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "sql": sql,
                "explanation": explanation
            }


class GetSchemaTool(BaseTool):
    """获取数据库 Schema 的工具"""

    name = "get_database_schema"
    description = "Retrieve the schema of all tables in the database"

    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "table_names": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional: specific table names to retrieve. If empty, returns all tables."
                    }
                }
            }
        }

    async def execute(self, table_names: list = None, **kwargs) -> Dict[str, Any]:
        """
        获取数据库 Schema

        Args:
            table_names: 要获取的表名列表（为空则返回所有表）

        Returns:
            {
                "success": bool,
                "schema": Dict[str, List[Dict]],
                "table_count": int
            }
        """
        try:
            all_schema = await self.adapter.get_schema()

            if table_names:
                # 只返回指定的表
                schema = {table: all_schema[table] for table in table_names if table in all_schema}
            else:
                schema = all_schema

            return {
                "success": True,
                "schema": schema,
                "table_count": len(schema),
                "tables": list(schema.keys())
            }

        except Exception as e:
            logger.error("get_schema_failed", error=str(e))
            return {
                "success": False,
                "error": str(e)
            }
