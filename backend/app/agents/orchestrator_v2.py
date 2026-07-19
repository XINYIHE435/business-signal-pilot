"""
Orchestrator V2 - 使用真正的 Intent Classifier 和 SQL Agent

集成 Phase 2 实现的 Agents
"""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from datetime import datetime, date
import operator
import structlog
import json

from langgraph.graph import StateGraph, END
from app.agents.intent_classifier import intent_classifier_node
from app.agents.sql_agent import sql_agent_node
from app.agents.diagnosis_agent import (
    hypothesis_generator_node,
    tool_router_node,
    evidence_collection_node,
    reasoning_node,
    KNOWN_SITES,
)

logger = structlog.get_logger()


# === Agent State 定义 ===
class AgentState(TypedDict):
    """全局状态，在所有节点间流转"""

    # 输入
    user_query: str
    session_id: str
    conversation_history: List[Dict]

    # 意图理解
    intent: str
    entities: Dict[str, Any]

    # Tool 调用记录
    tool_calls: Annotated[List[Dict], operator.add]
    tool_results: Annotated[List[Dict], operator.add]

    # 推理轨迹
    reasoning_trace: Annotated[List[Dict], operator.add]

    # 诊断 Agent 相关（Phase 3）
    analysis_mode: str            # "root_cause" | "comparison"
    hypotheses: List[Dict]        # 生成的假设
    selected_tools: List[str]     # Tool Router 选中的工具
    evidence: List[Dict]          # 收集到的证据
    diagnosis_report: Dict[str, Any]  # 最终诊断报告

    # 报告 Agent 相关（Phase 4）
    report_content: Dict[str, Any]  # 生成的报告内容
    report_request: Dict[str, Any]  # 统一的报告请求参数（site/category/marketplace/report_type/start_date/end_date）
    missing_report_params: List[str]  # Parameter Validation 检测到缺失的必要参数

    # 输出
    final_response: Dict[str, Any]
    should_end: bool


# === ReportRequest 参数解析辅助函数（Parameter Validation） ===

_SITE_CN_MAP: Dict[str, str] = {
    "美国": "US", "德国": "DE", "英国": "UK", "澳大利亚": "AU", "澳洲": "AU",
    "法国": "FR", "意大利": "IT", "西班牙": "ES", "加拿大": "CA",
    "中国": "CN", "日本": "JP",
}

_CN_DIGIT = {"一": 1, "二": 2, "三": 3, "四": 4, "1": 1, "2": 2, "3": 3, "4": 4}

_CLARIFICATION_QUESTIONS = {
    "site": "请问需要查询哪个站点？（例如：US、DE、UK 等）",
    "date_range": "请问报告的时间范围是？（例如：过去一个月、2025年7月、2025年Q1等）",
}


def _extract_site_strict(text: str) -> Optional[str]:
    """从文本中提取站点代码，找不到时返回 None（不给默认值，交由缺参校验处理）"""
    import re
    if not text:
        return None
    for cn_name, code in _SITE_CN_MAP.items():
        if cn_name in text:
            return code
    upper = str(text).upper()
    for tok in re.split(r"[^A-Z]+", upper):
        if tok in KNOWN_SITES:
            return tok
    return None


def _is_iso_date(value: Any) -> bool:
    """校验是否为合法的 YYYY-MM-DD 字符串（用于甄别 Intent 返回的占位符，如 'past_month'/'now'）"""
    import re
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(value or "")))


def _month_end(year: int, month: int) -> date:
    import calendar
    return date(year, month, calendar.monthrange(year, month)[1])


def _infer_report_type(span_days: int) -> str:
    """根据时间跨度推断报告类型标签（仅用于展示，不参与日期计算）"""
    if span_days <= 10:
        return "weekly"
    if span_days <= 45:
        return "monthly"
    if span_days <= 100:
        return "quarterly"
    return "custom"


def _resolve_date_range_from_text(text: str, business_date: date):
    """
    从原始用户文本中确定性解析时间范围，严禁使用 datetime.now() 或默认过去一周/一个月。

    支持：
    - 绝对时间：YYYY年MM月 / YYYY年第N季度 / YYYY年QN
    - 相对时间（基于真实 business_date 计算，而非系统时钟）：
      本周/上周、本月/上月、过去N天、过去N周、过去N个月等

    Returns:
        (start_date, end_date, inferred_report_type) 或 None（未能从文本中识别出时间范围）
    """
    import re
    from datetime import timedelta

    text = text or ""

    # 绝对：YYYY年MM月
    m = re.search(r"(\d{4})\s*年\s*(\d{1,2})\s*月", text)
    if m:
        year, month = int(m.group(1)), int(m.group(2))
        if 1 <= month <= 12:
            return date(year, month, 1), _month_end(year, month), "monthly"

    # 绝对：YYYY年第N季度 / YYYY年QN
    m = (
        re.search(r"(\d{4})\s*年.{0,4}第?\s*([1-4一二三四])\s*季度", text)
        or re.search(r"(\d{4})\s*年.{0,4}[Qq]\s*([1-4])", text)
    )
    if m:
        year = int(m.group(1))
        q = _CN_DIGIT.get(m.group(2))
        if q:
            start_month = (q - 1) * 3 + 1
            return date(year, start_month, 1), _month_end(year, start_month + 2), "quarterly"

    # 相对：本周/这周
    if re.search(r"(本周|这周|这个星期)", text):
        return business_date - timedelta(days=6), business_date, "weekly"

    # 相对：上周/上星期
    if re.search(r"(上周|上星期|上个星期)", text):
        end = business_date - timedelta(days=7)
        return end - timedelta(days=6), end, "weekly"

    # 相对：本月/这个月
    if re.search(r"(本月|这个月)", text):
        return business_date.replace(day=1), business_date, "monthly"

    # 相对：上月/上个月
    if re.search(r"(上月|上个月)", text):
        end = business_date.replace(day=1) - timedelta(days=1)
        return end.replace(day=1), end, "monthly"

    # 相对：过去/最近/近 N 天
    m = re.search(r"(?:过去|最近|近)\s*(\d+)\s*天", text)
    if m:
        days = int(m.group(1))
        return business_date - timedelta(days=days - 1), business_date, _infer_report_type(days)

    # 相对：过去/最近/近 N(或一) 周/星期
    m = re.search(r"(?:过去|最近|近)\s*(\d+|一)\s*(?:个)?\s*(?:周|星期)", text)
    if m:
        n = 1 if m.group(1) == "一" else int(m.group(1))
        return business_date - timedelta(days=n * 7 - 1), business_date, _infer_report_type(n * 7)

    # 相对：过去/最近/近 N(或一) 个月
    m = re.search(r"(?:过去|最近|近)\s*(\d+|一)\s*个?\s*月", text)
    if m:
        n = 1 if m.group(1) == "一" else int(m.group(1))
        return business_date - timedelta(days=n * 30 - 1), business_date, _infer_report_type(n * 30)

    return None


def _build_report_request(state: Dict, business_date: date) -> Dict[str, Any]:
    """
    统一构建 ReportRequest：Chat 与 Dashboard 都产出同一种结构，供下游 SQL Agent 直接消费。

    时间范围解析规则（严禁默认回退到"过去一周/一个月"）：
    1. 优先对用户原始输入文本做确定性正则解析（相对时间基于真实 business_date 计算，
       绝对时间如 "2025年7月"/"2025年Q1" 直接解析），不依赖 LLM 自行做日期运算。
    2. 仅当正则未能从文本中识别、且 Intent 抽取的 date_range 恰好是合法 ISO 日期时，才作为兜底
       （Intent 有时会返回 'past_month'/'now' 等占位符而非真实日期，此类值一律不采信）。
    3. 两者都未命中时，start_date/end_date 保持 None，交由 Parameter Validation 判定缺失并询问用户。
    """
    entities = state.get("entities", {})
    query_text = state.get("user_query", "")

    site = _extract_site_strict(str(entities.get("site", "") or "")) or _extract_site_strict(query_text)

    resolved = _resolve_date_range_from_text(query_text, business_date)
    if resolved:
        start_date, end_date, report_type = resolved
        start_date, end_date = str(start_date), str(end_date)
    else:
        date_range = entities.get("date_range") or {}
        raw_start, raw_end = date_range.get("start"), date_range.get("end")
        if _is_iso_date(raw_start) and _is_iso_date(raw_end):
            start_date, end_date = raw_start, raw_end
            span_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
            report_type = _infer_report_type(span_days)
        else:
            start_date, end_date, report_type = None, None, entities.get("report_type") or None

    return {
        "site": site,
        "category": entities.get("category") or "",
        "marketplace": site,  # 本平台 marketplace 即 site（eBay 站点代码）
        "report_type": report_type,
        "start_date": start_date,
        "end_date": end_date,
        "source": "chat",
    }


def _missing_report_params(report_request: Dict[str, Any]) -> List[str]:
    """检查 ReportRequest 是否缺少生成报告所需的必要参数（至少 site 与 date_range）"""
    missing = []
    if not report_request.get("site"):
        missing.append("site")
    if not report_request.get("start_date") or not report_request.get("end_date"):
        missing.append("date_range")
    return missing


# === Parameter Validation Node ===

def parameter_validation_node(state: Dict) -> Dict:
    """
    Parameter Validation 节点 —— Report Agent 前置校验

    确保生成报告所需的必要参数（至少 site、date_range）完整后才允许进入 SQL 查询。
    缺失时不允许回退到默认"过去一周/一个月"，而是暂停当前 Workflow，
    由 Synthesizer 生成澄清问题通过 Chat 主动询问用户；用户在下一轮补充参数后，
    Intent Classifier 结合对话历史重新提取实体，本节点会用新的实体再次尝试构建 ReportRequest。
    """
    from app.core.database_v2 import db_v2

    business_date = db_v2.get_max_date()
    if business_date is None:
        logger.error("parameter_validation_no_business_date")
        return {
            "report_request": {},
            "missing_report_params": [],
            "report_content": {
                "success": False,
                "clarification_needed": False,
                "error": "数据库中无业务数据，无法生成报告",
            },
        }

    report_request = _build_report_request(state, business_date)
    missing = _missing_report_params(report_request)

    logger.info(
        "parameter_validation",
        site=report_request.get("site"),
        start_date=report_request.get("start_date"),
        end_date=report_request.get("end_date"),
        missing=missing,
    )

    if missing:
        question = "；".join(_CLARIFICATION_QUESTIONS[m] for m in missing)
        return {
            "report_request": report_request,
            "missing_report_params": missing,
            "report_content": {
                "success": False,
                "clarification_needed": True,
                "missing_params": missing,
                "question": question,
            },
            "reasoning_trace": [{
                "node": "parameter_validation",
                "timestamp": datetime.now().isoformat(),
                "missing_params": missing,
            }]
        }

    return {
        "report_request": report_request,
        "missing_report_params": [],
        "reasoning_trace": [{
            "node": "parameter_validation",
            "timestamp": datetime.now().isoformat(),
            "missing_params": [],
            "site": report_request["site"],
            "start_date": report_request["start_date"],
            "end_date": report_request["end_date"],
        }]
    }


# === Report Agent 数据采集辅助函数 ===

def _get_report_db():
    """创建报告用的 Database Adapter + Tool（复用 SQL Agent 的连接模式）"""
    from pathlib import Path
    from app.adapters.database import DuckDBAdapter
    from app.tools.database_tool import DatabaseTool
    from app.core.config import settings

    project_root = Path(__file__).parent.parent.parent.parent
    db_path = project_root / settings.database_path
    if not db_path.exists():
        raise FileNotFoundError(f"Database file not found: {db_path}")

    adapter = DuckDBAdapter(str(db_path), read_only=False)
    return adapter, DatabaseTool(adapter)


async def _report_category_where(adapter, category: str) -> str:
    """解析品类过滤条件（兼容 L1/L2），返回 SQL AND 子句或空串"""
    if not category:
        return ""
    cat = str(category).replace("'", "''")  # 简单转义，避免引号破坏 SQL
    # 优先匹配 L2（更精确），再匹配 L1
    rows = await adapter.execute(
        f"SELECT category_id_l2 AS id FROM daily_metrics WHERE category_l2 ILIKE '%{cat}%' LIMIT 1"
    )
    if rows and rows[0].get("id") is not None:
        return f" AND category_id_l2 = {int(rows[0]['id'])}"
    rows = await adapter.execute(
        f"SELECT category_id_l1 AS id FROM daily_metrics WHERE category_l1 ILIKE '%{cat}%' LIMIT 1"
    )
    if rows and rows[0].get("id") is not None:
        return f" AND category_id_l1 = {int(rows[0]['id'])}"
    return ""


async def _kpi_snapshot(db_tool, site: str, cat_where: str, start_date, end_date) -> Dict[str, Any]:
    """查询单个时间窗口的聚合 KPI"""
    sql = f"""
        SELECT
            SUM(gmv) AS gmv,
            SUM(sold_items) AS sold_items,
            SUM(orders) AS orders,
            AVG(ctr) AS ctr,
            AVG(cvr) AS cvr,
            SUM(gmv) / NULLIF(SUM(sold_items), 0) AS asp
        FROM daily_metrics
        WHERE site = '{site}'{cat_where}
          AND date >= '{start_date}'
          AND date <= '{end_date}'
    """
    result = await db_tool.execute(sql=sql, explanation=f"{site} KPI {start_date}~{end_date}")
    if result.get("success") and result.get("data"):
        row = result["data"][0]
        return {k: (float(v) if v is not None else 0.0) for k, v in row.items()}
    return {}


# KPI 指标展示配置：字段名 → (中文名, 是否货币, 是否百分比)
_KPI_METRICS = [
    ("gmv", "GMV", True, False),
    ("orders", "订单数", False, False),
    ("sold_items", "销量(SI)", False, False),
    ("cvr", "转化率(CVR)", False, True),
    ("ctr", "点击率(CTR)", False, True),
    ("asp", "客单价(ASP)", True, False),
]


def _fmt_kpi_value(field: str, value: float, is_currency: bool, is_pct: bool) -> str:
    """格式化 KPI 展示值"""
    if is_currency:
        return f"${value:,.2f}"
    if is_pct:
        return f"{value * 100:.2f}%"
    return f"{value:,.0f}"


def _build_kpi_items(cur: Dict[str, Any], prev: Dict[str, Any]) -> List[Dict[str, Any]]:
    """基于当前/上期数据构建 KPI 列表，含真实变化率与趋势"""
    items = []
    for field, name, is_currency, is_pct in _KPI_METRICS:
        cur_val = cur.get(field, 0.0) or 0.0
        prev_val = prev.get(field, 0.0) or 0.0
        if prev_val:
            change_pct = ((cur_val - prev_val) / prev_val) * 100
        else:
            change_pct = 0.0
        trend = "上升" if change_pct > 0.5 else ("下降" if change_pct < -0.5 else "持平")
        items.append({
            "field": field,
            "metric_name": name,
            "current_value": _fmt_kpi_value(field, cur_val, is_currency, is_pct),
            "current_raw": cur_val,
            "previous_raw": prev_val,
            "change_percentage": f"{change_pct:+.1f}%",
            "change_pct_num": change_pct,
            "trend": trend,
        })
    return items


# 需要触发根因诊断的核心指标及其下降阈值（百分比）
_ANOMALY_METRICS = {"gmv": -10.0, "orders": -10.0, "cvr": -10.0}


def _detect_anomalies(kpi_items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """检测 KPI 中的明显下降（GMV/订单/CVR 跌幅超过阈值）"""
    anomalies = []
    for item in kpi_items:
        threshold = _ANOMALY_METRICS.get(item["field"])
        if threshold is not None and item["change_pct_num"] <= threshold:
            anomalies.append({
                "metric": item["field"],
                "metric_name": item["metric_name"],
                "change_percentage": item["change_percentage"],
            })
    return anomalies


async def _trend_series(db_tool, site: str, cat_where: str, start_date, end_date) -> List[Dict[str, Any]]:
    """查询每日 GMV/订单趋势（用于 Key Findings）"""
    sql = f"""
        SELECT date,
               SUM(gmv) AS gmv,
               SUM(orders) AS orders,
               SUM(sold_items) AS sold_items
        FROM daily_metrics
        WHERE site = '{site}'{cat_where}
          AND date >= '{start_date}'
          AND date <= '{end_date}'
        GROUP BY date
        ORDER BY date
    """
    result = await db_tool.execute(sql=sql, explanation=f"{site} trend {start_date}~{end_date}")
    if result.get("success"):
        return result.get("data", [])
    return []


async def _run_diagnosis_for_report(
    site: str, category: str, start_date, end_date, anomalies: List[Dict]
) -> Dict[str, Any]:
    """
    异常触发时调用 Diagnosis Agent（复用其 async 核心逻辑），返回诊断报告
    """
    from app.agents.diagnosis_agent import (
        generate_hypotheses,
        collect_evidence,
        reason_diagnosis,
        HYPOTHESIS_TOOL_MAP,
    )

    metric_names = "、".join(a["metric_name"] for a in anomalies)
    diag_query = f"为什么{site}站{('的' + category) if category else ''}的{metric_names}在{start_date}至{end_date}期间下降了？"
    diag_entities = {
        "site": site,
        "category": category,
        "metric": anomalies[0]["metric"] if anomalies else "gmv",
        "date_range": {"start": str(start_date), "end": str(end_date)},
    }

    # 1) 生成假设
    hyp_result = await generate_hypotheses(diag_query, diag_entities, "root_cause")
    hypotheses = hyp_result.get("hypotheses", [])

    # 2) Tool 路由
    selected_tools: List[str] = []
    for hyp in hypotheses:
        for tool_name in HYPOTHESIS_TOOL_MAP.get(hyp.get("type"), []):
            if tool_name not in selected_tools:
                selected_tools.append(tool_name)

    # 3) 收集证据
    evidence = await collect_evidence(selected_tools, hypotheses, diag_entities, "root_cause")

    # 4) 推理
    report = await reason_diagnosis(diag_query, diag_entities, hypotheses, evidence, "root_cause")
    return report


async def _gather_report_data(state: Dict, report_request: Dict[str, Any]) -> Dict[str, Any]:
    """
    Report Agent 的核心数据采集：直接消费 ReportRequest 中已由 Parameter Validation
    确定的 start_date/end_date/site/category，真实执行 SQL 查询 KPI/趋势，
    检测异常，必要时调用 Diagnosis Agent 获取根因。

    严禁在此处使用 datetime.now() 或 report_type 推导时间窗口 —— 时间范围必须
    完全来自 report_request（用户指定或 Parameter Validation 校验通过的值）。
    """
    from datetime import timedelta

    site = report_request["site"]
    category = report_request.get("category") or ""
    start_date = date.fromisoformat(report_request["start_date"])
    end_date = date.fromisoformat(report_request["end_date"])

    adapter, db_tool = _get_report_db()

    # 上一同长度周期，用于环比
    span_days = (end_date - start_date).days + 1
    prev_end = start_date - timedelta(days=1)
    prev_start = prev_end - timedelta(days=span_days - 1)

    cat_where = await _report_category_where(adapter, category)

    # KPI：当前周期 + 上一周期
    cur = await _kpi_snapshot(db_tool, site, cat_where, start_date, end_date)
    prev = await _kpi_snapshot(db_tool, site, cat_where, prev_start, prev_end)
    kpi_items = _build_kpi_items(cur, prev)

    data_available = bool(cur) and (cur.get("gmv", 0) or cur.get("orders", 0) or cur.get("sold_items", 0))

    trend_data = await _trend_series(db_tool, site, cat_where, start_date, end_date) if data_available else []
    anomalies = _detect_anomalies(kpi_items) if data_available else []

    # 根因：优先复用 state 中已有诊断，否则异常时触发诊断
    root_causes: List[Dict] = []
    diagnosis_report: Dict[str, Any] = {}
    existing = state.get("diagnosis_report", {})
    if existing and existing.get("success"):
        root_causes = existing.get("root_causes", [])
        diagnosis_report = existing
        logger.info("report_reusing_diagnosis", root_cause_count=len(root_causes))
    elif anomalies:
        logger.info("report_triggering_diagnosis", anomalies=[a["metric"] for a in anomalies])
        diag = await _run_diagnosis_for_report(site, category, start_date, end_date, anomalies)
        if diag.get("success"):
            root_causes = diag.get("root_causes", [])
            diagnosis_report = diag

    return {
        "start_date": str(start_date),
        "end_date": str(end_date),
        "kpi_items": kpi_items,
        "trend_data": trend_data,
        "anomalies": anomalies,
        "root_causes": root_causes,
        "diagnosis_report": diagnosis_report,
        "data_available": bool(data_available),
    }


# === Report Agent Node ===

async def _report_agent_core(state: Dict) -> Dict:
    """
    报告生成核心逻辑（async）- 生成周报/月报/季报/自定义区间报告

    作为 SQL Agent 与 Diagnosis Agent 的消费者，直接消费 Parameter Validation
    节点产出的 report_request（site/category/start_date/end_date 均已确定）：
    1. 用 ReportRequest 中的真实参数执行 SQL 查询，获取 KPI 与趋势
    2. 检测 KPI 是否存在明显下降（GMV/订单/CVR）
    3. 若存在异常，自动调用 Diagnosis Agent 获取 Root Causes / Evidence
    4. 基于真实数据用 LLM 生成 Executive Summary

    被两处调用：
    - report_agent_node（LangGraph 同步节点，内部用 asyncio.run 调用本函数）
    - run_dashboard_report（本身已是 async 函数，直接 await 本函数）
    """
    from anthropic import Anthropic
    from app.core.config import settings

    logger.info("report_agent_node_started")

    report_request = state.get("report_request") or {}
    site = report_request.get("site")
    category = report_request.get("category") or ""
    report_type = report_request.get("report_type") or "custom"

    # Parameter Validation 应已保证参数完整；此处仅做防御性兜底
    if not site or not report_request.get("start_date") or not report_request.get("end_date"):
        logger.error("report_agent_missing_report_request", report_request=report_request)
        return {
            "report_content": {"error": "报告请求参数不完整，无法生成报告", "success": False},
        }

    # 真实采集数据：SQL 查询 KPI/趋势 +（可选）诊断
    try:
        gathered = await _gather_report_data(state, report_request)
    except Exception as e:
        logger.error("report_data_gathering_failed", error=str(e))
        return {
            "report_content": {"error": f"数据采集失败: {e}", "success": False},
            "reasoning_trace": [{
                "node": "report_agent",
                "timestamp": datetime.now().isoformat(),
                "action": "gather_report_data",
                "success": False,
                "error": str(e),
            }]
        }

    start_date = gathered["start_date"]
    end_date = gathered["end_date"]
    kpi_items = gathered["kpi_items"]
    trend_data = gathered["trend_data"]
    anomalies = gathered["anomalies"]
    root_causes = gathered["root_causes"]
    data_available = gathered["data_available"]

    # SQL 确实返回空结果时才返回"暂无数据"
    if not data_available:
        logger.warning("report_no_data", site=site, category=category, window=f"{start_date}~{end_date}")
        return {
            "report_content": {
                "success": False,
                "error": f"查询无数据：{site} 站在 {start_date} 至 {end_date} 期间无业务记录",
                "report_type": report_type,
                "start_date": start_date,
                "end_date": end_date,
            },
            "reasoning_trace": [{
                "node": "report_agent",
                "timestamp": datetime.now().isoformat(),
                "action": "gather_report_data",
                "success": True,
                "data_available": False,
            }]
        }

    # 供 LLM 使用的精简数据上下文（真实 SQL 结果）
    kpi_data = [{
        "metric_name": k["metric_name"],
        "current_value": k["current_value"],
        "change_percentage": k["change_percentage"],
        "trend": k["trend"],
    } for k in kpi_items]
    trend_sample = trend_data[-14:] if isinstance(trend_data, list) else []

    # 使用LLM生成Executive Summary
    if not settings.anthropic_api_key:
        logger.error("anthropic_api_key_not_configured")
        return {
            "report_content": {
                "error": "Claude API未配置",
                "success": False
            },
            "reasoning_trace": [{
                "node": "report_agent",
                "timestamp": datetime.now().isoformat(),
                "action": "generate_executive_summary",
                "success": False,
                "error": "Claude API未配置"
            }]
        }

    client = Anthropic(api_key=settings.anthropic_api_key, base_url=settings.ANTHROPIC_BASE_URL)

    # 定义Executive Summary结构化输出schema
    executive_summary_tool = {
        "name": "generate_executive_summary",
        "description": "生成包含6个固定部分的Executive Summary",
        "input_schema": {
            "type": "object",
            "properties": {
                "overall_business_performance": {
                    "type": "string",
                    "description": "整体业务表现总结（基于提供的KPI数据）"
                },
                "kpi_summary": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "metric_name": {"type": "string"},
                            "current_value": {"type": "string"},
                            "trend": {"type": "string", "enum": ["上升", "下降", "持平"]},
                            "change_percentage": {"type": "string"}
                        },
                        "required": ["metric_name", "current_value", "trend"]
                    },
                    "description": "关键指标汇总（必须来自提供的SQL数据）"
                },
                "key_findings": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "关键发现（必须基于SQL查询的实际数据，禁止编造）"
                },
                "root_causes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "cause": {"type": "string"},
                            "confidence": {"type": "string"},
                            "evidence": {"type": "string"}
                        },
                        "required": ["cause", "confidence"]
                    },
                    "description": "根本原因（优先引用Diagnosis Agent的结果，如无则标注'待分析'）"
                },
                "recommended_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "action": {"type": "string"},
                            "priority": {"type": "string", "enum": ["高", "中", "低"]},
                            "expected_impact": {"type": "string"}
                        },
                        "required": ["action", "priority"]
                    },
                    "description": "推荐行动（按优先级排序）"
                },
                "next_week_focus": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "下周重点关注事项"
                }
            },
            "required": [
                "overall_business_performance",
                "kpi_summary",
                "key_findings",
                "root_causes",
                "recommended_actions",
                "next_week_focus"
            ]
        }
    }

    scope_desc = f"{site} 站" + (f" · {category} 品类" if category else " · 全品类")
    anomaly_desc = (
        "、".join(f"{a['metric_name']}({a['change_percentage']})" for a in anomalies)
        if anomalies else "无明显异常"
    )

    prompt = f"""你是业务分析专家，需要生成一份{report_type}业务报告的Executive Summary。

报告范围: {scope_desc}
报告时间范围: {start_date} 至 {end_date}（对比上一同长度周期）

真实数据（均来自 SQL 查询，禁止编造）:
1. KPI 汇总（含环比变化与趋势）:
{json.dumps(kpi_data, ensure_ascii=False, indent=2)}

2. 每日趋势明细（最近数据）:
{json.dumps(trend_sample, ensure_ascii=False, indent=2, default=str)}

3. 检测到的指标异常: {anomaly_desc}

4. 根因分析结果（来自 Diagnosis Agent）:
{json.dumps(root_causes, ensure_ascii=False, indent=2, default=str) if root_causes else "无（本期无明显异常，未触发根因诊断）"}

重要要求:
- kpi_summary 必须逐条使用上面提供的 KPI 数据（metric_name/current_value/trend/change_percentage 直接采用，禁止改写数字）
- key_findings 必须基于 KPI 变化与趋势明细中的真实数字，指出具体指标的升降幅度
- root_causes: 若上面提供了根因分析结果，必须引用其 cause/confidence/evidence；若为"无"，则说明本期无明显异常、无需深度归因
- recommended_actions 需针对实际数据表现给出可执行、具体的建议，并标注优先级
- next_week_focus 结合本期表现给出下周应重点跟踪的指标
- 保持专业、简洁的商务语言

请调用generate_executive_summary工具生成结构化报告。"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}],
            tools=[executive_summary_tool],
            tool_choice={"type": "tool", "name": "generate_executive_summary"}
        )

        # 提取Tool Call结果
        tool_call = response.content[0] if response.content else None
        if tool_call and hasattr(tool_call, "input"):
            summary = tool_call.input
        else:
            summary = {"error": "LLM未返回有效的结构化输出"}

        reused_diagnosis = bool(state.get("diagnosis_report", {}).get("success"))
        report_content = {
            "report_type": report_type,
            "start_date": start_date,
            "end_date": end_date,
            "site": site,
            "category": category,
            "executive_summary": summary,
            "generated_at": datetime.now().isoformat(),
            "data_sources": {
                "reused_diagnosis": reused_diagnosis,
                "triggered_diagnosis": bool(root_causes) and not reused_diagnosis,
                "fresh_query": True,
                "anomalies": [a["metric"] for a in anomalies],
            }
        }

        logger.info(
            "report_generated",
            report_type=report_type,
            site=site,
            kpi_count=len(kpi_items),
            root_cause_count=len(root_causes),
        )

        updates = {
            "report_content": report_content,
            "reasoning_trace": [{
                "node": "report_agent",
                "timestamp": datetime.now().isoformat(),
                "action": "generate_executive_summary",
                "success": True,
                "kpi_count": len(kpi_items),
                "anomaly_count": len(anomalies),
                "root_cause_count": len(root_causes),
            }]
        }
        # 若本节点触发了诊断，将诊断报告写入 state（供导出层/前端复用）
        if gathered.get("diagnosis_report") and not state.get("diagnosis_report", {}).get("success"):
            updates["diagnosis_report"] = gathered["diagnosis_report"]
        return updates

    except Exception as e:
        logger.error("report_generation_failed", error=str(e))
        return {
            "report_content": {
                "error": str(e),
                "success": False
            },
            "reasoning_trace": [{
                "node": "report_agent",
                "timestamp": datetime.now().isoformat(),
                "action": "generate_executive_summary",
                "success": False,
                "error": str(e)
            }]
        }


def report_agent_node(state: Dict) -> Dict:
    """
    Report Agent Node for LangGraph（同步包装）

    LangGraph 在独立线程池中执行同步节点，因此内部 asyncio.run 是安全的
    （与 sql_agent_node/diagnosis_agent 节点组遵循相同模式）。
    """
    import asyncio
    return asyncio.run(_report_agent_core(state))


# === Synthesizer Node ===

def synthesizer_node(state: Dict) -> Dict:
    """
    结果综合节点 - 格式化最终响应
    """
    intent = state["intent"]
    tool_results = state.get("tool_results", [])

    logger.info("synthesizing_response", intent=intent, result_count=len(tool_results))

    # 根据意图格式化响应
    if intent == "data_query" and tool_results:
        # 数据查询结果
        sql_result = tool_results[0]

        if sql_result.get("success"):
            response = {
                "type": "data_query",
                "success": True,
                "data": sql_result.get("data", []),
                "sql": sql_result.get("sql", ""),
                "explanation": sql_result.get("explanation", ""),
                "row_count": sql_result.get("row_count", 0),
                "message": f"查询成功，返回 {sql_result.get('row_count', 0)} 行数据"
            }
        else:
            response = {
                "type": "data_query",
                "success": False,
                "error": sql_result.get("error", "Unknown error"),
                "message": "查询失败"
            }

    elif intent in ("root_cause_analysis", "comparison_analysis"):
        # 根因分析 / 对比分析（Phase 3 - Diagnosis Agent）
        report = state.get("diagnosis_report", {})
        response = {
            "type": "diagnosis",
            "success": report.get("success", False),
            "analysis_mode": report.get("analysis_mode", "root_cause"),
            "summary": report.get("summary", ""),
            "hypotheses": state.get("hypotheses", []),
            "root_causes": report.get("root_causes", []),
            "contributions": report.get("contributions", []),
            "recommended_actions": report.get("recommended_actions", []),
            "evidence": report.get("evidence", state.get("evidence", [])),
            "comparison": report.get("comparison"),
            "message": report.get("summary", "诊断完成"),
        }
        if not report.get("success", False) and report.get("error"):
            response["error"] = report["error"]

    elif intent == "report_generation":
        # 报告生成结果
        report = state.get("report_content", {})
        if report.get("clarification_needed"):
            # Parameter Validation 检测到必要参数缺失，暂停并通过 Chat 主动询问用户
            response = {
                "type": "clarification_needed",
                "success": False,
                "missing_params": report.get("missing_params", []),
                "question": report.get("question", ""),
                "message": report.get("question", "请补充报告所需的参数"),
            }
        elif report.get("error"):
            response = {
                "type": "report",
                "success": False,
                "error": report.get("error"),
                "message": "报告生成失败"
            }
        else:
            response = {
                "type": "report",
                "success": True,
                "report_type": report.get("report_type", "weekly"),
                "start_date": report.get("start_date", ""),
                "end_date": report.get("end_date", ""),
                "executive_summary": report.get("executive_summary", {}),
                "generated_at": report.get("generated_at", ""),
                "data_sources": report.get("data_sources", {}),
                "message": f"{report.get('report_type', 'weekly')}报告生成成功"
            }

    else:
        response = {
            "type": "unknown",
            "success": False,
            "message": f"暂不支持此类查询: {intent}"
        }

    return {
        "final_response": response,
        "should_end": True,
        "reasoning_trace": [{
            "node": "synthesizer",
            "timestamp": datetime.now().isoformat(),
            "response_type": response["type"],
            "success": response.get("success", False)
        }]
    }


# === Workflow 构建 ===

def create_orchestrator_v2() -> StateGraph:
    """
    创建 Orchestrator V2 Workflow

    流程: intent_classifier → sql_agent → synthesizer → END
    报告生成路径: intent_classifier → parameter_validation →（缺参则直接 synthesizer 询问用户，
                 否则）report_agent → synthesizer → END
    """
    workflow = StateGraph(AgentState)

    # 添加节点
    workflow.add_node("intent_classifier", intent_classifier_node)
    workflow.add_node("sql_agent", sql_agent_node)

    # Diagnosis Agent 节点组（Phase 3）
    workflow.add_node("hypothesis_generator", hypothesis_generator_node)
    workflow.add_node("tool_router", tool_router_node)
    workflow.add_node("evidence_collection", evidence_collection_node)
    workflow.add_node("reasoning", reasoning_node)

    # Report Agent 节点（Phase 4）+ 前置的 Parameter Validation 节点
    workflow.add_node("parameter_validation", parameter_validation_node)
    workflow.add_node("report_agent", report_agent_node)

    workflow.add_node("synthesizer", synthesizer_node)

    # 设置入口
    workflow.set_entry_point("intent_classifier")

    # 条件路由（根据意图）
    def route_by_intent(state: Dict) -> str:
        """根据意图决定下一步"""
        intent = state.get("intent", "data_query")

        if intent == "data_query":
            return "sql_agent"
        elif intent in ("root_cause_analysis", "comparison_analysis"):
            # Diagnosis Agent 入口
            return "hypothesis_generator"
        elif intent == "report_generation":
            # Report Agent 入口（先经过 Parameter Validation）
            return "parameter_validation"
        else:
            return "synthesizer"

    workflow.add_conditional_edges(
        "intent_classifier",
        route_by_intent,
        {
            "sql_agent": "sql_agent",
            "hypothesis_generator": "hypothesis_generator",
            "parameter_validation": "parameter_validation",
            "synthesizer": "synthesizer"
        }
    )

    # SQL 查询路径
    workflow.add_edge("sql_agent", "synthesizer")

    # 诊断路径：hypothesis → tool_router → evidence → reasoning → synthesizer
    workflow.add_edge("hypothesis_generator", "tool_router")
    workflow.add_edge("tool_router", "evidence_collection")
    workflow.add_edge("evidence_collection", "reasoning")
    workflow.add_edge("reasoning", "synthesizer")

    # Parameter Validation：参数完整才进入 report_agent，否则直接去 synthesizer 生成澄清问题
    def route_after_validation(state: Dict) -> str:
        return "synthesizer" if state.get("missing_report_params") else "report_agent"

    workflow.add_conditional_edges(
        "parameter_validation",
        route_after_validation,
        {"report_agent": "report_agent", "synthesizer": "synthesizer"}
    )

    # 报告路径：report_agent → synthesizer
    workflow.add_edge("report_agent", "synthesizer")

    workflow.add_edge("synthesizer", END)

    logger.info("orchestrator_v2_created")

    return workflow


def compile_orchestrator_v2():
    """编译 Orchestrator V2"""
    workflow = create_orchestrator_v2()
    app = workflow.compile()

    logger.info("orchestrator_v2_compiled")

    return app


# === 便捷执行函数 ===

async def run_query(
    query: str,
    session_id: str = "default",
    conversation_history: List[Dict] = None
) -> Dict[str, Any]:
    """
    执行查询（使用 Orchestrator V2）

    Args:
        query: 用户查询
        session_id: 会话 ID
        conversation_history: 对话历史

    Returns:
        {
            "response": Dict,
            "reasoning_trace": List[Dict],
            "tool_calls": List[Dict],
            "intent": str,
            "entities": Dict
        }
    """
    app = compile_orchestrator_v2()

    # 初始状态
    initial_state = {
        "user_query": query,
        "session_id": session_id,
        "conversation_history": conversation_history or [],
        "intent": "",
        "entities": {},
        "tool_calls": [],
        "tool_results": [],
        "reasoning_trace": [],
        "analysis_mode": "",
        "hypotheses": [],
        "selected_tools": [],
        "evidence": [],
        "diagnosis_report": {},
        "report_content": {},
        "report_request": {},
        "missing_report_params": [],
        "final_response": {},
        "should_end": False
    }

    # 执行 workflow
    logger.info("executing_orchestrator_v2", query=query[:50])

    try:
        final_state = await app.ainvoke(initial_state)

        return {
            "response": final_state["final_response"],
            "reasoning_trace": final_state["reasoning_trace"],
            "tool_calls": final_state["tool_calls"],
            "intent": final_state["intent"],
            "entities": final_state["entities"]
        }

    except Exception as e:
        logger.error("orchestrator_v2_failed", error=str(e))
        return {
            "response": {
                "type": "error",
                "success": False,
                "error": str(e),
                "message": "查询执行失败"
            },
            "reasoning_trace": [],
            "tool_calls": [],
            "intent": "unknown",
            "entities": {}
        }


async def run_dashboard_report(
    site: str,
    start_date: str,
    end_date: str,
    category: str = "",
    report_type: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Dashboard 报告生成入口

    与 Chat 入口（run_query）共用同一个 ReportRequest 结构与 report_agent_node/
    synthesizer_node 逻辑，唯一区别：Dashboard 传入的参数视为完整可信，
    直接跳过 Parameter Validation（不会触发澄清询问）。

    Args:
        site: 站点代码（如 DE、US）
        start_date: 起始日期（YYYY-MM-DD）
        end_date: 结束日期（YYYY-MM-DD）
        category: 品类（可选）
        report_type: 报告类型标签（可选，未提供时按时间跨度自动推断）

    Returns:
        与 run_query 相同结构：{"response", "reasoning_trace", "tool_calls", "intent", "entities"}
    """
    span_days = (date.fromisoformat(end_date) - date.fromisoformat(start_date)).days + 1
    report_request = {
        "site": site,
        "category": category or "",
        "marketplace": site,
        "report_type": report_type or _infer_report_type(span_days),
        "start_date": start_date,
        "end_date": end_date,
        "source": "dashboard",
    }

    state: Dict[str, Any] = {
        "user_query": f"[dashboard] {site} {start_date}~{end_date}",
        "session_id": "dashboard",
        "conversation_history": [],
        "intent": "report_generation",
        "entities": {},
        "tool_calls": [],
        "tool_results": [],
        "reasoning_trace": [],
        "analysis_mode": "",
        "hypotheses": [],
        "selected_tools": [],
        "evidence": [],
        "diagnosis_report": {},
        "report_content": {},
        "report_request": report_request,
        "missing_report_params": [],
        "final_response": {},
        "should_end": False,
    }

    logger.info("executing_dashboard_report", site=site, start_date=start_date, end_date=end_date)

    try:
        # 直接 await 核心逻辑（本函数已在事件循环中，不能再嵌套 asyncio.run）
        report_update = await _report_agent_core(state)
        state["reasoning_trace"] = state["reasoning_trace"] + report_update.get("reasoning_trace", [])
        state["report_content"] = report_update.get("report_content", {})
        if report_update.get("diagnosis_report"):
            state["diagnosis_report"] = report_update["diagnosis_report"]

        synth_update = synthesizer_node(state)
        state["reasoning_trace"] = state["reasoning_trace"] + synth_update.get("reasoning_trace", [])
        state["final_response"] = synth_update.get("final_response", {})

        return {
            "response": state["final_response"],
            "reasoning_trace": state["reasoning_trace"],
            "tool_calls": state["tool_calls"],
            "intent": state["intent"],
            "entities": state["entities"],
        }
    except Exception as e:
        logger.error("dashboard_report_failed", error=str(e))
        return {
            "response": {
                "type": "error",
                "success": False,
                "error": str(e),
                "message": "报告生成失败",
            },
            "reasoning_trace": [],
            "tool_calls": [],
            "intent": "report_generation",
            "entities": {},
        }
