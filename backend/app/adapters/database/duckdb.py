"""
DuckDB Adapter - DuckDB 数据库适配器实现
"""

import duckdb
from pathlib import Path
from typing import Any, Dict, List, Optional
import structlog

from .base import DatabaseAdapter

logger = structlog.get_logger()


class DuckDBAdapter(DatabaseAdapter):
    """DuckDB 适配器"""

    def __init__(self, db_path: str, read_only: bool = False):
        """
        初始化 DuckDB 连接

        Args:
            db_path: 数据库文件路径
            read_only: 是否只读模式
        """
        self.db_path = Path(db_path)
        self.read_only = read_only
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

        if not self.db_path.exists():
            logger.error("database_not_found", path=str(self.db_path))
            raise FileNotFoundError(f"Database file not found: {self.db_path}")

        self._connect()

    def _connect(self) -> None:
        """建立数据库连接"""
        if self._conn is None:
            self._conn = duckdb.connect(str(self.db_path), read_only=self.read_only)
            logger.info("duckdb_connected", path=str(self.db_path), read_only=self.read_only)

    async def execute(self, sql: str, params: tuple = None) -> List[Dict[str, Any]]:
        """
        执行 SQL 查询

        Args:
            sql: SQL 语句
            params: 查询参数

        Returns:
            查询结果（字典列表）
        """
        try:
            if params:
                result = self._conn.execute(sql, params).fetchdf()
            else:
                result = self._conn.execute(sql).fetchdf()

            # 转换为字典列表
            data = result.to_dict(orient='records')

            logger.debug(
                "sql_executed",
                sql=sql[:100],
                row_count=len(data),
                has_params=params is not None
            )

            return data

        except Exception as e:
            logger.error("sql_execution_failed", sql=sql[:100], error=str(e))
            raise

    async def get_schema(self) -> Dict[str, List[Dict[str, str]]]:
        """
        获取数据库 Schema

        Returns:
            {table_name: [{name, type, notnull, ...}]}
        """
        tables = await self.list_tables()
        schema = {}

        for table in tables:
            try:
                # 使用 PRAGMA table_info 获取列信息
                columns_result = self._conn.execute(f"PRAGMA table_info({table})").fetchall()

                columns = []
                for col in columns_result:
                    # col: (cid, name, type, notnull, dflt_value, pk)
                    columns.append({
                        "name": col[1],
                        "type": col[2],
                        "notnull": bool(col[3]),
                        "default": col[4],
                        "primary_key": bool(col[5])
                    })

                schema[table] = columns

            except Exception as e:
                logger.error("get_table_schema_failed", table=table, error=str(e))

        logger.debug("schema_retrieved", table_count=len(schema))
        return schema

    async def list_tables(self) -> List[str]:
        """
        列出所有表

        Returns:
            表名列表
        """
        result = self._conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        tables = [row[0] for row in result]
        logger.debug("tables_listed", count=len(tables))

        return tables

    def close(self) -> None:
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("duckdb_closed")
