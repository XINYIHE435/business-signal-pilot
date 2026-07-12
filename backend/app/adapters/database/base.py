"""
Database Adapter - 数据库抽象层基类

支持多种数据库后端，Agent 无需关心具体实现
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, List


class DatabaseAdapter(ABC):
    """数据库适配器基类"""

    @abstractmethod
    async def execute(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数（可选）

        Returns:
            查询结果列表（每行为一个字典）
        """
        pass

    @abstractmethod
    async def get_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取数据库 Schema

        Returns:
            {
                "table_name": [
                    {"name": "column_name", "type": "column_type", ...},
                    ...
                ],
                ...
            }
        """
        pass

    @abstractmethod
    async def list_tables(self) -> List[str]:
        """
        列出所有表名

        Returns:
            表名列表
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """关闭数据库连接"""
        pass
