"""
核心模块初始化
"""

from app.core.config import settings
from app.core.database_v2 import db_v2 as db
from app.core.llm import llm_client

__all__ = ["settings", "db", "llm_client"]
