"""
Diagnosis Agent 测试（Phase 3）

覆盖：
- Tool Router 映射逻辑（纯函数，无需 LLM/DB）
- 站点解析（root_cause / comparison）
- Mock Tool 层（JSON + DuckDB 真实表）
- 证据收集与端到端诊断流程（依赖数据库，缺失则跳过）
"""

import os
import pytest

from app.agents.diagnosis_agent import (
    tool_router_node,
    _resolve_comparison_sites,
    _extract_sites,
    _resolve_analysis_mode,
    HYPOTHESIS_TYPES,
    HYPOTHESIS_TOOL_MAP,
)

_HAS_DB = os.path.exists("data/signal.db") or os.path.exists("../data/signal.db")


# === 纯函数测试（无外部依赖） ===

def test_hypothesis_tool_map_covers_all_types():
    """每种假设类型都应有对应的 Tool 映射"""
    for hyp_type in HYPOTHESIS_TYPES:
        assert hyp_type in HYPOTHESIS_TOOL_MAP
        assert len(HYPOTHESIS_TOOL_MAP[hyp_type]) > 0


def test_tool_router_selects_tools_from_hypotheses():
    """Tool Router 根据假设去重选择工具"""
    hypotheses = [
        {"type": "traffic"},
        {"type": "campaign"},
        {"type": "traffic"},  # 重复，应去重
        {"type": "competition"},
    ]
    update = tool_router_node({"hypotheses": hypotheses})
    tools = update["selected_tools"]

    assert "execute_sql" in tools       # traffic
    assert "query_campaigns" in tools   # campaign
    assert "query_news" in tools        # competition
    # 去重：execute_sql 只出现一次
    assert tools.count("execute_sql") == 1


def test_tool_router_empty_hypotheses():
    """空假设应返回空工具列表"""
    update = tool_router_node({"hypotheses": []})
    assert update["selected_tools"] == []


def test_extract_sites_handles_comma_separated():
    """classifier 可能把两个站点塞进一个字段"""
    assert _extract_sites("DE, US") == ["DE", "US"]
    assert _extract_sites("US") == ["US"]
    assert _extract_sites("DE vs US") == ["DE", "US"]  # 从 comparison 文本抽取
    assert _extract_sites("德国 vs 美国") == []          # 纯中文无合法站点代码
    assert _extract_sites("") == []


def test_resolve_comparison_sites():
    """对比模式解析出两个站点，保序去重"""
    assert _resolve_comparison_sites({"site": "DE, US"}) == ["DE", "US"]
    assert _resolve_comparison_sites({"site": "DE", "comparison": "vs US"}) == ["DE", "US"]
    # 兜底：不足两个时补齐
    result = _resolve_comparison_sites({"site": "DE"})
    assert len(result) == 2
    assert "DE" in result


def test_resolve_analysis_mode():
    """intent 决定分析模式"""
    assert _resolve_analysis_mode({"intent": "comparison_analysis"}) == "comparison"
    assert _resolve_analysis_mode({"intent": "root_cause_analysis"}) == "root_cause"
    assert _resolve_analysis_mode({"intent": "data_query"}) == "root_cause"


# === Mock Tool 层测试 ===

@pytest.mark.asyncio
async def test_json_mock_tools():
    """JSON mock 工具（holiday/policy/news）无需数据库即可运行"""
    from app.tools.diagnosis_tools import HolidayTool, PolicyTool, NewsTool

    holiday = await HolidayTool().execute(site="DE", start_date="2026-07-01", end_date="2026-07-31")
    assert holiday["success"] is True
    assert holiday["hypothesis_type"] == "holiday"

    policy = await PolicyTool().execute(site="DE", category_l1="Electronics",
                                        start_date="2026-07-01", end_date="2026-07-31")
    assert policy["success"] is True
    # POL-2026-014 应命中
    assert any("authenticity" in p.get("title", "").lower() for p in policy["data"])

    news = await NewsTool().execute(site="DE", category_l1="Electronics",
                                    start_date="2026-07-01", end_date="2026-07-31")
    assert news["success"] is True
    assert news["hypothesis_type"] == "competition"


@pytest.mark.skipif(not _HAS_DB, reason="Database file not found")
@pytest.mark.asyncio
async def test_db_backed_tools():
    """DuckDB 真实表工具"""
    from app.adapters.database import DuckDBAdapter
    from app.tools.diagnosis_tools import InventoryTool, SellerTool

    db_path = "data/signal.db" if os.path.exists("data/signal.db") else "../data/signal.db"
    # 与进程内既有连接保持相同配置（DuckDB 不允许同文件不同配置的连接共存）
    adapter = DuckDBAdapter(db_path, read_only=False)

    inv = await InventoryTool(adapter).execute(
        site="DE", category_l1="Electronics", start_date="2026-07-01", end_date="2026-07-12"
    )
    assert inv["success"] is True
    assert inv["hypothesis_type"] == "inventory"

    seller = await SellerTool(adapter).execute(
        site="DE", category_l1="Electronics", start_date="2026-07-01", end_date="2026-07-12"
    )
    assert seller["success"] is True
    assert seller["row_count"] >= 0


@pytest.mark.skipif(not _HAS_DB, reason="Database file not found")
@pytest.mark.asyncio
async def test_collect_evidence_root_cause():
    """证据收集：单站点收集不报错并带 site 标记"""
    from app.agents.diagnosis_agent import collect_evidence

    evidence = await collect_evidence(
        selected_tools=["execute_sql", "query_inventory"],
        hypotheses=[{"type": "traffic"}, {"type": "inventory"}],
        entities={"site": "DE", "category": "Electronics"},
        analysis_mode="root_cause",
    )
    assert isinstance(evidence, list)
    assert all("site" in ev for ev in evidence)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
