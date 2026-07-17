"""
Diagnosis Agent - 根因分析与对比分析 Agent

实现完整的诊断闭环：
    Hypothesis Generation → Tool Routing → Evidence Collection → LLM Reasoning

支持两种分析模式（共用同一套节点）：
- root_cause: 根因分析（为什么 GMV 下降？）
- comparison: 对比分析（德国 vs 美国表现）

设计说明：
- 节点直接嵌入 Orchestrator V2 的主 StateGraph（见 orchestrator_v2.py）
- 遵循现有 Agent 模式：同步 node wrapper 内部用 asyncio.run 调用 async 逻辑
  （LangGraph 会在独立线程池中执行同步节点，因此内部 asyncio.run 是安全的）
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


# === 假设类型定义 ===
# 每种假设对应一类潜在的业务归因，后续由 Tool Router 映射到具体 Tool
HYPOTHESIS_TYPES = [
    "traffic",      # 流量变化（impressions/clicks/ctr）
    "campaign",     # 营销活动（促销开始/结束、预算变化）
    "seller",       # 卖家行为（头部卖家流失、份额变化）
    "inventory",    # 库存健康（缺货率、供应天数）
    "holiday",      # 节假日效应
    "policy",       # 平台政策变化
    "competition",  # 竞争/外部市场（新闻舆情）
]

# 假设类型 → 需要调用的 Tool 名称映射
# Task 2 会用到；此处先定义，Task 3 落地对应 Tool
HYPOTHESIS_TOOL_MAP: Dict[str, List[str]] = {
    "traffic": ["execute_sql"],
    "campaign": ["query_campaigns"],
    "seller": ["query_sellers"],
    "inventory": ["query_inventory"],
    "holiday": ["query_holidays"],
    "policy": ["query_policies"],
    "competition": ["query_news"],
}


# ============================================================
# Async 核心逻辑（Task 1 为骨架 stub，Task 2/4 填充真实实现）
# ============================================================

def _get_client():
    """获取 Claude 客户端（复用现有配置）"""
    from anthropic import AsyncAnthropic
    from app.core.config import settings

    if not settings.anthropic_api_key:
        return None
    return AsyncAnthropic(
        api_key=settings.anthropic_api_key,
        base_url=settings.ANTHROPIC_BASE_URL,
    )


def _hypothesis_tool_schema() -> Dict[str, Any]:
    """假设生成的 Tool Schema"""
    return {
        "name": "generate_hypotheses",
        "description": (
            "Generate ranked diagnostic hypotheses explaining a business metric "
            "change (root cause) or a performance gap between two sites (comparison)."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "hypotheses": {
                    "type": "array",
                    "description": "Ranked list of hypotheses, most likely first",
                    "items": {
                        "type": "object",
                        "properties": {
                            "type": {
                                "type": "string",
                                "enum": HYPOTHESIS_TYPES,
                                "description": "Hypothesis category",
                            },
                            "statement": {
                                "type": "string",
                                "description": "Concrete hypothesis, e.g. 'A major campaign ended, reducing traffic'",
                            },
                            "rationale": {
                                "type": "string",
                                "description": "Why this hypothesis is plausible given the query",
                            },
                            "prior_confidence": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                                "description": "Initial confidence before evidence collection",
                            },
                        },
                        "required": ["type", "statement", "prior_confidence"],
                    },
                }
            },
            "required": ["hypotheses"],
        },
    }


async def generate_hypotheses(
    query: str, entities: Dict[str, Any], analysis_mode: str
) -> Dict[str, Any]:
    """
    生成诊断假设（LLM Tool Calling）

    Args:
        query: 用户查询
        entities: 意图分类提取的实体（metric/site/category/date_range/comparison）
        analysis_mode: "root_cause" | "comparison"

    Returns:
        {"hypotheses": [{"type", "statement", "rationale", "prior_confidence"}, ...]}
    """
    client = _get_client()
    if not client:
        logger.warning("diagnosis_client_not_available_fallback")
        return {"hypotheses": _fallback_hypotheses(analysis_mode)}

    mode_desc = (
        "The user wants to understand WHY a metric changed (root cause analysis)."
        if analysis_mode == "root_cause"
        else "The user wants to COMPARE performance between two sites/segments and explain the gap."
    )

    system_prompt = f"""You are a senior business analyst for an eBay cross-border analytics platform.

{mode_desc}

Available hypothesis categories (choose the most relevant ones):
- traffic: changes in impressions/clicks/CTR
- campaign: promotions starting/ending, budget or discount changes
- seller: top-seller churn, seller share shifts, seller quality
- inventory: stock-outs, days-of-supply, listing health
- holiday: holiday/seasonal effects
- policy: platform policy changes affecting the category/site
- competition: competitive or external market events (news/sentiment)

Generate 3-5 prioritized hypotheses. Be specific and business-grounded.
Rank them by prior_confidence (most likely first). Use the extracted entities for context."""

    user_message = f"""User query: {query}

Extracted entities: {entities}
Analysis mode: {analysis_mode}

Generate diagnostic hypotheses."""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=1500,
            temperature=0.3,
            system=system_prompt,
            tools=[_hypothesis_tool_schema()],
            tool_choice={"type": "tool", "name": "generate_hypotheses"},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "generate_hypotheses":
                hypotheses = block.input.get("hypotheses", [])
                logger.info(
                    "hypotheses_generated",
                    mode=analysis_mode,
                    count=len(hypotheses),
                    types=[h.get("type") for h in hypotheses],
                )
                return {"hypotheses": hypotheses}

        logger.warning("no_hypothesis_tool_use")
        return {"hypotheses": _fallback_hypotheses(analysis_mode)}

    except Exception as e:
        logger.error("generate_hypotheses_failed", error=str(e))
        return {"hypotheses": _fallback_hypotheses(analysis_mode)}


def _fallback_hypotheses(analysis_mode: str) -> List[Dict[str, Any]]:
    """
    LLM 不可用时的备用假设（覆盖核心类别，保证下游流程可跑通）
    """
    base = [
        {"type": "traffic", "statement": "Traffic (impressions/clicks) shifted, driving the metric change",
         "rationale": "Traffic is the most common driver of GMV changes", "prior_confidence": 0.6},
        {"type": "campaign", "statement": "A marketing campaign started or ended in the period",
         "rationale": "Campaigns cause step-changes in GMV", "prior_confidence": 0.55},
        {"type": "seller", "statement": "Top seller behavior or share changed",
         "rationale": "Concentrated seller share makes GMV sensitive to top sellers", "prior_confidence": 0.5},
        {"type": "inventory", "statement": "Inventory health (stock-outs) constrained sales",
         "rationale": "Stock-outs directly cap GMV", "prior_confidence": 0.45},
    ]
    return base


def _ensure_diagnosis_tools():
    """
    确保诊断工具已注册到全局 registry（幂等）

    Returns:
        DatabaseAdapter 实例（供 traffic 查询直接使用）
    """
    from pathlib import Path
    from app.tools.registry import tool_registry
    from app.adapters.database import DuckDBAdapter
    from app.tools.diagnosis_tools import register_diagnosis_tools
    from app.tools.database_tool import DatabaseTool
    from app.core.config import settings

    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / settings.database_path
    adapter = DuckDBAdapter(str(db_path), read_only=False)

    if tool_registry.get("query_campaigns") is None:
        register_diagnosis_tools(adapter)
    if tool_registry.get("execute_sql") is None:
        tool_registry.register(DatabaseTool(adapter))

    return adapter


def _resolve_time_window(entities: Dict[str, Any]) -> tuple:
    """
    根据 business date 与 entities 解析诊断时间窗口

    默认取业务日期前 14 天。
    """
    from datetime import timedelta
    from app.core.database_v2 import db_v2

    end = db_v2.get_max_date()
    if end is None:
        return None, None

    days = 14
    date_range = str(entities.get("date_range", "") or "").lower()
    if "7" in date_range:
        days = 7
    elif "30" in date_range or "month" in date_range:
        days = 30
    elif "90" in date_range or "quarter" in date_range:
        days = 90

    start = end - timedelta(days=days)
    return start.isoformat(), end.isoformat()


KNOWN_SITES = ["US", "DE", "UK", "AU", "FR", "IT", "ES", "CA", "CN", "JP"]


def _extract_sites(text: str) -> List[str]:
    """
    从任意文本中按顺序抽取合法站点代码（去重）

    兼容以下形态：
    - "DE"            → ["DE"]
    - "DE, US"        → ["DE", "US"]   (classifier 常把两个站点塞进 site 字段)
    - "vs US" / "德国 vs 美国" → 从中匹配已知站点
    """
    import re

    found: List[str] = []
    upper = str(text or "").upper()
    # 用非字母边界切分，逐 token 校验，保留原始顺序
    tokens = re.split(r"[^A-Z]+", upper)
    for tok in tokens:
        if tok in KNOWN_SITES and tok not in found:
            found.append(tok)
    return found


def _resolve_comparison_sites(entities: Dict[str, Any]) -> List[str]:
    """
    对比模式下解析两个站点

    合并 entities.site 与 comparison 字段中出现的所有合法站点，保序去重。
    """
    sites: List[str] = []
    for field in ("site", "comparison"):
        for s in _extract_sites(entities.get(field, "")):
            if s not in sites:
                sites.append(s)

    # 兜底：确保至少两个站点
    for s in ["US", "DE"]:
        if len(sites) >= 2:
            break
        if s not in sites:
            sites.append(s)

    return sites[:2]


async def _query_traffic(adapter, site: str, category_l1, start_date, end_date) -> Dict[str, Any]:
    """
    直接查询 daily_metrics 的流量与转化指标（traffic 假设的证据）
    """
    where = [f"site = '{site}'"]
    if category_l1:
        where.append(f"category_l1 = '{category_l1}'")
    if start_date and end_date:
        where.append(f"date >= '{start_date}' AND date <= '{end_date}'")
    where_clause = " AND ".join(where)

    sql = f"""
        SELECT date,
               SUM(gmv) AS gmv,
               SUM(impressions) AS impressions,
               SUM(clicks) AS clicks,
               AVG(ctr) AS ctr,
               AVG(cvr) AS cvr,
               SUM(sold_items) AS sold_items
        FROM daily_metrics
        WHERE {where_clause}
        GROUP BY date
        ORDER BY date DESC
        LIMIT 30
    """
    from app.tools.diagnosis_tools import _clean_rows
    try:
        rows = await adapter.execute(sql)
        return {
            "success": True,
            "tool": "execute_sql",
            "hypothesis_type": "traffic",
            "site": site,
            "row_count": len(rows),
            "data": _clean_rows(rows),
        }
    except Exception as e:
        logger.error("traffic_query_failed", error=str(e))
        return {"success": False, "tool": "execute_sql", "hypothesis_type": "traffic", "site": site, "error": str(e)}


async def _collect_for_site(
    adapter, selected_tools: List[str], site: str, category_l1, start_date, end_date
) -> List[Dict[str, Any]]:
    """为单个站点并行调用所有选中的 Tool"""
    import asyncio
    from app.tools.registry import tool_registry

    tasks = []
    tool_order = []
    for tool_name in selected_tools:
        if tool_name == "execute_sql":
            tasks.append(_query_traffic(adapter, site, category_l1, start_date, end_date))
        else:
            tool = tool_registry.get(tool_name)
            if tool is None:
                continue
            tasks.append(tool.execute(
                site=site, category_l1=category_l1,
                start_date=start_date, end_date=end_date,
            ))
        tool_order.append(tool_name)

    results = await asyncio.gather(*tasks, return_exceptions=True)

    evidence = []
    for tool_name, res in zip(tool_order, results):
        if isinstance(res, Exception):
            evidence.append({"success": False, "tool": tool_name, "site": site, "error": str(res)})
        else:
            res.setdefault("site", site)
            evidence.append(res)
    return evidence


async def collect_evidence(
    selected_tools: List[str],
    hypotheses: List[Dict],
    entities: Dict[str, Any],
    analysis_mode: str,
) -> List[Dict[str, Any]]:
    """
    并行调用选中的 Tool 收集证据

    - root_cause: 针对单站点收集
    - comparison: 针对两个站点分别收集
    """
    if not selected_tools:
        return []

    adapter = _ensure_diagnosis_tools()
    category_l1 = entities.get("category")
    start_date, end_date = _resolve_time_window(entities)

    if analysis_mode == "comparison":
        sites = _resolve_comparison_sites(entities)
    else:
        single = _extract_sites(entities.get("site", ""))
        sites = [single[0] if single else "US"]

    all_evidence: List[Dict[str, Any]] = []
    for site in sites:
        site_evidence = await _collect_for_site(
            adapter, selected_tools, site, category_l1, start_date, end_date
        )
        all_evidence.extend(site_evidence)

    logger.info(
        "evidence_collected",
        mode=analysis_mode,
        sites=sites,
        evidence_count=len(all_evidence),
        window=f"{start_date}~{end_date}",
    )
    return all_evidence


def _diagnosis_report_schema() -> Dict[str, Any]:
    """结构化诊断报告的 Tool Schema"""
    return {
        "name": "emit_diagnosis_report",
        "description": "Emit a structured diagnosis report grounded in the collected evidence",
        "input_schema": {
            "type": "object",
            "properties": {
                "summary": {
                    "type": "string",
                    "description": "2-4 sentence executive summary of the diagnosis (in the user's language)",
                },
                "root_causes": {
                    "type": "array",
                    "description": "Ranked root causes, each backed by evidence",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cause": {"type": "string", "description": "The root cause statement"},
                            "hypothesis_type": {"type": "string", "enum": HYPOTHESIS_TYPES},
                            "confidence": {"type": "number", "minimum": 0, "maximum": 1},
                            "evidence": {"type": "string", "description": "Concrete evidence supporting this cause"},
                            "contribution": {"type": "number", "minimum": 0, "maximum": 1,
                                             "description": "Estimated share of the total change (0-1)"},
                        },
                        "required": ["cause", "confidence", "evidence"],
                    },
                },
                "contributions": {
                    "type": "array",
                    "description": "Dimensional contribution breakdown (site/category/seller)",
                    "items": {
                        "type": "object",
                        "properties": {
                            "dimension": {"type": "string"},
                            "value": {"type": "string"},
                            "contribution_percent": {"type": "number"},
                            "change": {"type": "number"},
                        },
                        "required": ["dimension", "value", "contribution_percent"],
                    },
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Concrete, prioritized recommended actions",
                },
                "comparison": {
                    "type": "object",
                    "description": "Only for comparison mode: the head-to-head summary",
                    "properties": {
                        "site_a": {"type": "string"},
                        "site_b": {"type": "string"},
                        "winner": {"type": "string"},
                        "key_differences": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            "required": ["summary", "root_causes", "recommended_actions"],
        },
    }


def _compact_evidence(evidence: List[Dict]) -> str:
    """将证据压缩为适合放入 prompt 的文本（限制体积）"""
    import json as _json

    lines = []
    for ev in evidence:
        header = f"[{ev.get('hypothesis_type', '?')}] tool={ev.get('tool')} site={ev.get('site')} success={ev.get('success')} rows={ev.get('row_count', 0)}"
        data = ev.get("data", [])
        # 每个证据最多保留前 8 行，避免 prompt 过长
        sample = data[:8] if isinstance(data, list) else data
        lines.append(header + "\n" + _json.dumps(sample, ensure_ascii=False, default=str))
    return "\n\n".join(lines) if lines else "(no evidence collected)"


async def reason_diagnosis(
    query: str,
    entities: Dict[str, Any],
    hypotheses: List[Dict],
    evidence: List[Dict],
    analysis_mode: str,
) -> Dict[str, Any]:
    """
    基于证据进行 LLM 推理，输出结构化诊断报告

    root_cause 与 comparison 共用同一推理流程，仅 prompt 与 schema 字段有所侧重。
    """
    client = _get_client()

    empty_report = {
        "success": False,
        "analysis_mode": analysis_mode,
        "summary": "",
        "root_causes": [],
        "contributions": [],
        "recommended_actions": [],
        "evidence": evidence,
        "hypotheses": hypotheses,
    }

    if not client:
        empty_report["error"] = "LLM client not configured"
        empty_report["summary"] = "无法生成诊断报告：LLM 未配置"
        return empty_report

    mode_instruction = (
        "Diagnose the ROOT CAUSE of the metric change. Rank causes by confidence and estimate each cause's contribution."
        if analysis_mode == "root_cause"
        else "Perform a COMPARISON analysis between the two sites. Explain the performance gap, fill the 'comparison' field, and treat each driver as a root cause."
    )

    system_prompt = f"""You are a senior business diagnostician for an eBay cross-border analytics platform.

{mode_instruction}

Rules:
- Ground EVERY conclusion in the provided evidence. Do not invent numbers.
- If evidence is weak or missing for a hypothesis, lower its confidence accordingly.
- Reply in the SAME language as the user's query.
- Be concrete and business-actionable.
- You MUST call the emit_diagnosis_report tool."""

    hypotheses_text = "\n".join(
        f"- [{h.get('type')}] {h.get('statement')} (prior={h.get('prior_confidence')})"
        for h in hypotheses
    ) or "(none)"

    user_message = f"""User query: {query}
Analysis mode: {analysis_mode}
Entities: {entities}

Generated hypotheses:
{hypotheses_text}

Collected evidence:
{_compact_evidence(evidence)}

Produce the structured diagnosis report now."""

    try:
        response = await client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2500,
            temperature=0.2,
            system=system_prompt,
            tools=[_diagnosis_report_schema()],
            tool_choice={"type": "tool", "name": "emit_diagnosis_report"},
            messages=[{"role": "user", "content": user_message}],
        )

        for block in response.content:
            if block.type == "tool_use" and block.name == "emit_diagnosis_report":
                report = dict(block.input)
                report.update({
                    "success": True,
                    "analysis_mode": analysis_mode,
                    "evidence": evidence,
                    "hypotheses": hypotheses,
                })
                report.setdefault("contributions", [])
                logger.info(
                    "diagnosis_reasoned",
                    mode=analysis_mode,
                    root_cause_count=len(report.get("root_causes", [])),
                )
                return report

        empty_report["error"] = "No report tool_use in response"
        empty_report["summary"] = "诊断推理未返回结构化报告"
        return empty_report

    except Exception as e:
        logger.error("reason_diagnosis_failed", error=str(e))
        empty_report["error"] = str(e)
        empty_report["summary"] = f"诊断推理失败: {e}"
        return empty_report


# ============================================================
# LangGraph 节点包装（同步 wrapper，内部 asyncio.run 调用 async 逻辑）
# ============================================================

def _resolve_analysis_mode(state: Dict) -> str:
    """
    根据 intent 推断分析模式

    Returns:
        "root_cause" | "comparison"
    """
    intent = state.get("intent", "")
    if intent == "comparison_analysis":
        return "comparison"
    return "root_cause"


# === Node 1: Hypothesis Generator ===

def hypothesis_generator_node(state: Dict) -> Dict:
    """
    假设生成节点

    Task 1: 仅编排骨架，返回空假设列表
    Task 2: 接入 LLM 自动生成 Hypothesis
    """
    import asyncio

    analysis_mode = _resolve_analysis_mode(state)
    query = state["user_query"]
    entities = state.get("entities", {})

    logger.info("hypothesis_generation_started", mode=analysis_mode, query=query[:50])

    try:
        result = asyncio.run(generate_hypotheses(query, entities, analysis_mode))
        hypotheses = result.get("hypotheses", [])
    except Exception as e:
        logger.error("hypothesis_generation_failed", error=str(e))
        hypotheses = []

    return {
        "analysis_mode": analysis_mode,
        "hypotheses": hypotheses,
        "reasoning_trace": [{
            "node": "hypothesis_generator",
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": analysis_mode,
            "hypothesis_count": len(hypotheses),
            "hypotheses": hypotheses,
        }]
    }


# === Node 2: Tool Router ===

def tool_router_node(state: Dict) -> Dict:
    """
    Tool 路由节点

    根据生成的 Hypothesis 决定需要调用哪些 Tool（只路由，不执行）
    """
    hypotheses = state.get("hypotheses", [])

    selected_tools: List[str] = []
    for hyp in hypotheses:
        hyp_type = hyp.get("type") if isinstance(hyp, dict) else None
        for tool_name in HYPOTHESIS_TOOL_MAP.get(hyp_type, []):
            if tool_name not in selected_tools:
                selected_tools.append(tool_name)

    logger.info("tool_routing_completed", selected_tools=selected_tools)

    return {
        "selected_tools": selected_tools,
        "reasoning_trace": [{
            "node": "tool_router",
            "timestamp": datetime.now().isoformat(),
            "selected_tools": selected_tools,
        }]
    }


# === Node 3: Evidence Collection ===

def evidence_collection_node(state: Dict) -> Dict:
    """
    证据收集节点

    Task 1: 骨架，返回空证据
    Task 4: 并行调用选中的 Tool 并聚合 Evidence
    """
    import asyncio

    selected_tools = state.get("selected_tools", [])
    hypotheses = state.get("hypotheses", [])
    entities = state.get("entities", {})
    analysis_mode = state.get("analysis_mode", "root_cause")

    logger.info("evidence_collection_started", tool_count=len(selected_tools))

    try:
        evidence = asyncio.run(
            collect_evidence(selected_tools, hypotheses, entities, analysis_mode)
        )
    except Exception as e:
        logger.error("evidence_collection_failed", error=str(e))
        evidence = []

    tool_calls = [{
        "tool": ev.get("tool", "unknown"),
        "timestamp": datetime.now().isoformat(),
        "success": ev.get("success", False),
    } for ev in evidence]

    return {
        "evidence": evidence,
        "tool_calls": tool_calls,
        "tool_results": evidence,
        "reasoning_trace": [{
            "node": "evidence_collection",
            "timestamp": datetime.now().isoformat(),
            "evidence_count": len(evidence),
        }]
    }


# === Node 4: Reasoning ===

def reasoning_node(state: Dict) -> Dict:
    """
    推理节点

    Task 1: 骨架，返回占位报告
    Task 4: 基于 Evidence 用 LLM 输出结构化 Diagnosis Report
    """
    import asyncio

    query = state["user_query"]
    entities = state.get("entities", {})
    hypotheses = state.get("hypotheses", [])
    evidence = state.get("evidence", [])
    analysis_mode = state.get("analysis_mode", "root_cause")

    logger.info("reasoning_started", mode=analysis_mode, evidence_count=len(evidence))

    try:
        report = asyncio.run(
            reason_diagnosis(query, entities, hypotheses, evidence, analysis_mode)
        )
    except Exception as e:
        logger.error("reasoning_failed", error=str(e))
        report = {
            "success": False,
            "analysis_mode": analysis_mode,
            "error": str(e),
            "summary": "诊断推理失败",
            "root_causes": [],
            "contributions": [],
            "recommended_actions": [],
        }

    return {
        "diagnosis_report": report,
        "reasoning_trace": [{
            "node": "reasoning",
            "timestamp": datetime.now().isoformat(),
            "analysis_mode": analysis_mode,
            "success": report.get("success", False),
            "root_cause_count": len(report.get("root_causes", [])),
        }]
    }
