"""
Pydantic 数据模型

定义 API 请求和响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal


# ============================================================
# Dashboard Schemas
# ============================================================

class KPICard(BaseModel):
    """KPI 卡片"""
    name: str
    value: float
    change_percent: float
    trend: str  # "up" or "down"
    formatted_value: Optional[str] = None


class KPIResponse(BaseModel):
    """Dashboard KPI 响应"""
    kpis: List[KPICard]
    site: str
    category: Optional[str] = None
    date_range: str


class TrendPoint(BaseModel):
    """趋势数据点"""
    date: str
    value: float


class TrendResponse(BaseModel):
    """趋势图响应"""
    dates: List[str]
    gmv: List[float]
    sold_items: List[int]
    ctr: List[float]
    cvr: List[float]


class Anomaly(BaseModel):
    """异常记录"""
    date: str
    metric: str
    site: str
    category: str
    expected_value: float
    actual_value: float
    deviation_percent: float
    severity: str  # "low", "medium", "high", "critical"


class AnomalyResponse(BaseModel):
    """异常列表响应"""
    anomalies: List[Anomaly]
    total_count: int


# ============================================================
# Chat Schemas
# ============================================================

class ChatMessage(BaseModel):
    """聊天消息"""
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None


class ChatQueryRequest(BaseModel):
    """Chat 查询请求"""
    query: str = Field(..., min_length=1, max_length=500)
    session_id: Optional[str] = None
    context: Optional[List[ChatMessage]] = []


class ChatQueryResponse(BaseModel):
    """Chat 查询响应"""
    query_id: str
    response: str
    data: Optional[dict] = None
    chart: Optional[dict] = None
    execution_time_ms: int


# ============================================================
# Diagnosis Schemas
# ============================================================

class Contribution(BaseModel):
    """贡献度分析"""
    dimension: str  # "site", "category", "seller"
    value: str
    contribution_percent: float
    change: float


class RootCause(BaseModel):
    """根因假设"""
    cause: str
    confidence: float
    evidence: str
    contribution: float


class DiagnosisRequest(BaseModel):
    """诊断请求"""
    metric: str
    site: str
    category: Optional[str] = None
    date: str


class DiagnosisResponse(BaseModel):
    """诊断响应"""
    diagnosis_id: str
    metric: str
    site: str
    category: Optional[str] = None
    anomaly_score: float
    contributions: List[Contribution]
    root_causes: List[RootCause]
    recommended_actions: List[str]
    execution_time_ms: int


# ============================================================
# Report Schemas
# ============================================================

class ReportRequest(BaseModel):
    """报告生成请求"""
    report_type: str = "weekly"  # "weekly" or "monthly"
    start_date: str
    end_date: str
    sites: Optional[List[str]] = None
    categories: Optional[List[str]] = None


class ReportResponse(BaseModel):
    """报告响应"""
    report_id: str
    content: str  # Markdown 格式
    generated_at: datetime
    format: str = "markdown"


# ============================================================
# Common Schemas
# ============================================================

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    database_connected: bool
    llm_available: bool
    version: str


class ErrorResponse(BaseModel):
    """错误响应"""
    error: str
    detail: Optional[str] = None
    timestamp: datetime
