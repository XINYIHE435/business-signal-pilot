"""
Diagnosis API - 诊断分析接口（Phase 3）

提供两种入口：
- POST /api/v1/diagnosis/analyze : 结构化诊断（供 Dashboard 异常点击直接传参）
- Chat 对话查询仍走 /api/v1/chat/query（Orchestrator 自动路由到 Diagnosis Agent）

两者共用同一套 Diagnosis Agent 节点，保证结果一致。
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime
import structlog

from app.agents.diagnosis_agent import (
    generate_hypotheses,
    tool_router_node,
    collect_evidence,
    reason_diagnosis,
)

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/diagnosis", tags=["Diagnosis"])


# === Request/Response Models ===

class DiagnosisAnalyzeRequest(BaseModel):
    """诊断分析请求（Dashboard 异常点击场景）"""
    metric: str = "gmv"
    site: str
    category: Optional[str] = None
    date: Optional[str] = None
    mode: str = "root_cause"  # "root_cause" | "comparison"
    compare_site: Optional[str] = None  # comparison 模式下的对比站点
    question: Optional[str] = None      # 可选的自然语言问题（覆盖自动生成）


class DiagnosisAnalyzeResponse(BaseModel):
    """诊断分析响应"""
    success: bool
    analysis_mode: str
    summary: str
    hypotheses: List[Dict[str, Any]]
    root_causes: List[Dict[str, Any]]
    contributions: List[Dict[str, Any]]
    recommended_actions: List[str]
    comparison: Optional[Dict[str, Any]] = None
    evidence: List[Dict[str, Any]]
    reasoning_trace: List[Dict[str, Any]]
    timestamp: str


def _build_entities(req: DiagnosisAnalyzeRequest) -> Dict[str, Any]:
    """将请求映射为 Diagnosis Agent 使用的 entities"""
    entities: Dict[str, Any] = {"metric": req.metric, "site": req.site}
    if req.category:
        entities["category"] = req.category
    if req.date:
        entities["date_range"] = req.date
    if req.mode == "comparison" and req.compare_site:
        entities["comparison"] = f"{req.site} vs {req.compare_site}"
    return entities


def _build_query(req: DiagnosisAnalyzeRequest) -> str:
    """构造用于 LLM 推理的查询文本"""
    if req.question:
        return req.question
    cat = f" {req.category}" if req.category else ""
    if req.mode == "comparison" and req.compare_site:
        return f"Compare {req.metric.upper()} performance between {req.site} and {req.compare_site}{cat}"
    date_hint = f" around {req.date}" if req.date else ""
    return f"Why did {req.metric.upper()} change for {req.site}{cat}{date_hint}?"


@router.post("/analyze", response_model=DiagnosisAnalyzeResponse)
async def analyze(request: DiagnosisAnalyzeRequest):
    """
    执行诊断分析（Root Cause 或 Comparison）

    直接驱动 Diagnosis Agent 的四个阶段：
        Hypothesis → Tool Routing → Evidence Collection → Reasoning
    """
    try:
        analysis_mode = "comparison" if request.mode == "comparison" else "root_cause"
        entities = _build_entities(request)
        query = _build_query(request)

        logger.info("diagnosis_analyze_received", mode=analysis_mode, site=request.site, metric=request.metric)

        # 1) 生成假设
        hyp_result = await generate_hypotheses(query, entities, analysis_mode)
        hypotheses = hyp_result.get("hypotheses", [])

        # 2) 路由 Tool（复用节点逻辑，纯函数无副作用）
        route_update = tool_router_node({"hypotheses": hypotheses})
        selected_tools = route_update.get("selected_tools", [])

        # 3) 收集证据
        evidence = await collect_evidence(selected_tools, hypotheses, entities, analysis_mode)

        # 4) 推理
        report = await reason_diagnosis(query, entities, hypotheses, evidence, analysis_mode)

        reasoning_trace = [
            {"node": "hypothesis_generator", "hypothesis_count": len(hypotheses)},
            {"node": "tool_router", "selected_tools": selected_tools},
            {"node": "evidence_collection", "evidence_count": len(evidence)},
            {"node": "reasoning", "success": report.get("success", False)},
        ]

        return DiagnosisAnalyzeResponse(
            success=report.get("success", False),
            analysis_mode=analysis_mode,
            summary=report.get("summary", ""),
            hypotheses=hypotheses,
            root_causes=report.get("root_causes", []),
            contributions=report.get("contributions", []),
            recommended_actions=report.get("recommended_actions", []),
            comparison=report.get("comparison"),
            evidence=evidence,
            reasoning_trace=reasoning_trace,
            timestamp=datetime.now().isoformat(),
        )

    except Exception as e:
        logger.error("diagnosis_analyze_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Diagnosis failed: {str(e)}")


@router.get("/hypothesis-types")
async def list_hypothesis_types():
    """列出支持的假设类型"""
    from app.agents.diagnosis_agent import HYPOTHESIS_TYPES, HYPOTHESIS_TOOL_MAP
    return {
        "hypothesis_types": HYPOTHESIS_TYPES,
        "tool_map": HYPOTHESIS_TOOL_MAP,
    }
