"""
Dashboard API 测试
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_get_kpis_default():
    """测试获取默认 KPI（US 站点）"""
    response = client.get("/api/v1/dashboard/kpis")
    assert response.status_code == 200

    data = response.json()
    assert "kpis" in data
    assert "site" in data
    assert "date_range" in data

    # 验证返回了 5 个 KPI
    assert len(data["kpis"]) == 5

    # 验证 KPI 名称
    kpi_names = [kpi["name"] for kpi in data["kpis"]]
    assert "GMV" in kpi_names
    assert "SI" in kpi_names
    assert "CTR" in kpi_names
    assert "CVR" in kpi_names
    assert "ASP" in kpi_names

    # 验证每个 KPI 都有必要的字段
    for kpi in data["kpis"]:
        assert "name" in kpi
        assert "value" in kpi
        assert "change_percent" in kpi
        assert "trend" in kpi
        assert kpi["trend"] in ["up", "down"]


def test_get_kpis_with_site():
    """测试指定站点的 KPI"""
    response = client.get("/api/v1/dashboard/kpis?site=DE")
    assert response.status_code == 200

    data = response.json()
    assert data["site"] == "DE"
    assert len(data["kpis"]) == 5


def test_get_kpis_with_category():
    """测试指定品类的 KPI"""
    response = client.get("/api/v1/dashboard/kpis?site=US&category=Electronics")
    assert response.status_code == 200

    data = response.json()
    assert data["site"] == "US"
    assert data["category"] == "Electronics"


def test_get_trends_default():
    """测试获取默认趋势数据"""
    response = client.get("/api/v1/dashboard/trends")
    assert response.status_code == 200

    data = response.json()
    assert "dates" in data
    assert "gmv" in data
    assert "sold_items" in data
    assert "ctr" in data
    assert "cvr" in data

    # 验证数据长度一致
    dates_len = len(data["dates"])
    assert len(data["gmv"]) == dates_len
    assert len(data["sold_items"]) == dates_len
    assert len(data["ctr"]) == dates_len
    assert len(data["cvr"]) == dates_len

    # 默认是 30 天，但实际数据可能少于 30 天
    assert dates_len > 0
    assert dates_len <= 31


def test_get_trends_with_days():
    """测试指定天数的趋势"""
    response = client.get("/api/v1/dashboard/trends?days=7")
    assert response.status_code == 200

    data = response.json()
    dates_len = len(data["dates"])
    assert dates_len > 0
    assert dates_len <= 8


def test_get_trends_with_site_and_category():
    """测试指定站点和品类的趋势"""
    response = client.get("/api/v1/dashboard/trends?site=DE&category=Fashion&days=14")
    assert response.status_code == 200

    data = response.json()
    assert len(data["dates"]) > 0


def test_get_anomalies_default():
    """测试异常检测（默认参数）"""
    response = client.get("/api/v1/dashboard/anomalies")
    assert response.status_code == 200

    data = response.json()
    assert "anomalies" in data
    assert "total_count" in data
    assert isinstance(data["anomalies"], list)
    assert data["total_count"] >= 0

    # 验证异常数据结构
    if data["total_count"] > 0:
        anomaly = data["anomalies"][0]
        assert "date" in anomaly
        assert "metric" in anomaly
        assert "site" in anomaly
        assert "category" in anomaly
        assert "expected_value" in anomaly
        assert "actual_value" in anomaly
        assert "deviation_percent" in anomaly
        assert "severity" in anomaly
        assert anomaly["severity"] in ["low", "medium", "high", "critical"]


def test_get_anomalies_with_site():
    """测试指定站点的异常"""
    response = client.get("/api/v1/dashboard/anomalies?site=US")
    assert response.status_code == 200

    data = response.json()
    # 验证所有异常都属于 US 站点
    for anomaly in data["anomalies"]:
        assert anomaly["site"] == "US"


def test_get_anomalies_with_threshold():
    """测试不同阈值的异常检测"""
    # 较高阈值应该返回更少的异常
    response_high = client.get("/api/v1/dashboard/anomalies?threshold=0.30")
    response_low = client.get("/api/v1/dashboard/anomalies?threshold=0.10")

    assert response_high.status_code == 200
    assert response_low.status_code == 200

    high_count = response_high.json()["total_count"]
    low_count = response_low.json()["total_count"]

    # 较低阈值应该检测到更多异常
    assert low_count >= high_count


def test_api_error_handling():
    """测试 API 错误处理"""
    # 测试无效的参数
    response = client.get("/api/v1/dashboard/kpis?days=1000")  # 超过最大值
    assert response.status_code == 422  # Validation error
