"""
DuckDB 数据库连接管理
"""

import duckdb
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class Database:
    """DuckDB 连接管理器（单例模式）"""

    _instance = None
    _conn = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Database, cls).__new__(cls)
        return cls._instance

    def connect(self) -> duckdb.DuckDBPyConnection:
        """获取数据库连接"""
        if self._conn is None:
            db_path = Path(__file__).parent.parent.parent / settings.database_path

            if not db_path.exists():
                logger.error("database_not_found", path=str(db_path))
                raise FileNotFoundError(f"数据库文件不存在: {db_path}")

            self._conn = duckdb.connect(str(db_path), read_only=False)
            logger.info("database_connected", path=str(db_path))

        return self._conn

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.info("database_closed")

    def execute(self, query: str, params: tuple = None):
        """执行查询并返回结果"""
        conn = self.connect()

        try:
            if params:
                result = conn.execute(query, params).fetchall()
            else:
                result = conn.execute(query).fetchall()

            logger.debug("query_executed", query=query[:100])
            return result

        except Exception as e:
            logger.error("query_failed", query=query[:100], error=str(e))
            raise

    def execute_df(self, query: str, params: tuple = None):
        """执行查询并返回 DataFrame"""
        conn = self.connect()

        try:
            if params:
                result = conn.execute(query, params).df()
            else:
                result = conn.execute(query).df()

            logger.debug("query_executed_df", query=query[:100], rows=len(result))
            return result

        except Exception as e:
            logger.error("query_failed", query=query[:100], error=str(e))
            raise


# 全局数据库实例
db = Database()
