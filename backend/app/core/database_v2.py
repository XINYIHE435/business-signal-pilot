"""
DuckDB 数据库连接管理 V2

支持新的两级分类体系，同时保持向后兼容
"""

import duckdb
from pathlib import Path
from app.core.config import settings
import structlog

logger = structlog.get_logger()


class DatabaseV2:
    """DuckDB 连接管理器（V2 - 支持两级分类）"""

    _instance = None
    _conn = None
    _schema_version = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseV2, cls).__new__(cls)
        return cls._instance

    def connect(self) -> duckdb.DuckDBPyConnection:
        """获取数据库连接"""
        if self._conn is None:
            db_path = Path(__file__).parent.parent.parent.parent / settings.database_path

            if not db_path.exists():
                logger.error("database_not_found", path=str(db_path))
                raise FileNotFoundError(f"数据库文件不存在: {db_path}")

            self._conn = duckdb.connect(str(db_path), read_only=False)
            self._detect_schema_version()
            logger.info(
                "database_connected",
                path=str(db_path),
                schema_version=self._schema_version
            )

        return self._conn

    def _detect_schema_version(self):
        """检测数据库 Schema 版本"""
        try:
            # 检查是否有新字段 category_id_l1
            columns = self._conn.execute(
                "PRAGMA table_info(daily_metrics)"
            ).fetchall()

            column_names = [col[1] for col in columns]

            if 'category_id_l1' in column_names and 'category_id_l2' in column_names:
                self._schema_version = 'v2'
                logger.info("detected_schema_v2", columns=len(column_names))
            else:
                self._schema_version = 'v1'
                logger.info("detected_schema_v1", columns=len(column_names))

        except Exception as e:
            logger.warning("schema_detection_failed", error=str(e))
            self._schema_version = 'unknown'

    def is_v2_schema(self) -> bool:
        """判断是否是 V2 Schema"""
        if self._schema_version is None:
            self.connect()
        return self._schema_version == 'v2'

    def close(self):
        """关闭连接"""
        if self._conn:
            self._conn.close()
            self._conn = None
            self._schema_version = None
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

    def get_max_date(self):
        """
        获取数据库中的最大业务日期（Business Date）

        Returns:
            date: 数据库中最新的业务日期
        """
        try:
            result = self.execute("SELECT MAX(date) FROM daily_metrics")
            if result and result[0][0]:
                max_date = result[0][0]
                logger.info("max_date_fetched", max_date=str(max_date))
                return max_date
            else:
                logger.warning("no_data_in_daily_metrics")
                return None
        except Exception as e:
            logger.error("failed_to_get_max_date", error=str(e))
            return None

    def get_category_mapping(self, query_category: str = None):
        """
        获取分类映射

        如果是 V1 Schema，返回简单映射
        如果是 V2 Schema，返回 L1/L2 映射

        Args:
            query_category: 用户查询的分类名称（可能是 L1 或 L2）

        Returns:
            dict: 分类映射信息
        """
        if not self.is_v2_schema():
            # V1 Schema: 只有单级分类
            return {
                'version': 'v1',
                'category': query_category,
                'where_clause': f"category = '{query_category}'" if query_category else ""
            }

        # V2 Schema: 两级分类
        if not query_category:
            return {
                'version': 'v2',
                'where_clause': ""
            }

        # 尝试匹配 L1 或 L2
        conn = self.connect()

        # 先查 L2（更精确）
        result = conn.execute(f"""
            SELECT DISTINCT category_id_l1, category_l1, category_id_l2, category_l2
            FROM daily_metrics
            WHERE category_l2 ILIKE '%{query_category}%'
            LIMIT 1
        """).fetchone()

        if result:
            return {
                'version': 'v2',
                'match_level': 'l2',
                'category_id_l1': result[0],
                'category_l1': result[1],
                'category_id_l2': result[2],
                'category_l2': result[3],
                'where_clause': f"category_id_l2 = {result[2]}"
            }

        # 再查 L1
        result = conn.execute(f"""
            SELECT DISTINCT category_id_l1, category_l1
            FROM daily_metrics
            WHERE category_l1 ILIKE '%{query_category}%'
            LIMIT 1
        """).fetchone()

        if result:
            return {
                'version': 'v2',
                'match_level': 'l1',
                'category_id_l1': result[0],
                'category_l1': result[1],
                'where_clause': f"category_id_l1 = {result[0]}"
            }

        # 未找到匹配
        return {
            'version': 'v2',
            'match_level': 'none',
            'where_clause': ""
        }


# 全局数据库实例（V2）
db_v2 = DatabaseV2()
