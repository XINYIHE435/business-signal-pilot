"""
Database adapters package
"""

from app.adapters.database.base import DatabaseAdapter
from app.adapters.database.duckdb import DuckDBAdapter

__all__ = [
    "DatabaseAdapter",
    "DuckDBAdapter",
]
