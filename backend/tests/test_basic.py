"""
基础测试：验证 FastAPI 应用和数据库连接
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """测试根路径"""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert "version" in data


def test_health_check():
    """测试健康检查"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database_connected" in data
    assert "llm_available" in data
    assert "version" in data


def test_docs():
    """测试 API 文档可访问"""
    response = client.get("/docs")
    assert response.status_code == 200


def test_database_connection():
    """测试数据库连接"""
    from app.core.database_v2 import db_v2 as db

    # 测试简单查询
    result = db.execute("SELECT COUNT(*) FROM daily_metrics")
    assert result is not None
    assert len(result) > 0
    assert result[0][0] > 0  # 应该有数据


def test_database_query():
    """测试数据库查询功能"""
    from app.core.database_v2 import db_v2 as db

    # 查询站点列表
    result = db.execute("SELECT DISTINCT site FROM daily_metrics LIMIT 5")
    assert len(result) > 0

    # 查询品类列表
    result = db.execute("SELECT DISTINCT category FROM daily_metrics LIMIT 5")
    assert len(result) > 0
