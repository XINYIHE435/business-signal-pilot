"""
端到端测试 - Orchestrator V2

测试完整的查询流程：Intent Classifier → SQL Agent → Synthesizer
"""

import pytest
import os
from app.agents.orchestrator_v2 import run_query


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.path.exists("data/signal.db"),
    reason="Database file not found"
)
async def test_simple_data_query():
    """测试简单的数据查询"""
    result = await run_query("查询德国站的GMV")

    assert "response" in result
    assert "intent" in result
    assert result["intent"] in ["data_query", "comparison_analysis"]
    assert len(result["reasoning_trace"]) > 0


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.path.exists("data/signal.db"),
    reason="Database file not found"
)
async def test_data_query_with_date_range():
    """测试带日期范围的查询"""
    result = await run_query("过去7天德国站的GMV是多少？")

    assert result["response"]["type"] == "data_query"
    assert "entities" in result
    # 可能提取到 site 和 date_range
    entities = result["entities"]
    assert entities.get("site") in ["DE", None]


@pytest.mark.asyncio
async def test_diagnosis_query():
    """测试诊断类查询"""
    result = await run_query("为什么德国站GMV下降了15%？")

    assert result["intent"] == "root_cause_analysis"
    # 当前 Phase 2 未实现 Diagnosis Agent，应返回提示信息
    assert result["response"]["type"] == "diagnosis"


@pytest.mark.asyncio
async def test_report_query():
    """测试报告生成查询（site + 时间范围均已指定，应直接生成报告）"""
    result = await run_query("生成美国站本周业务报告")

    assert result["intent"] == "report_generation"
    assert result["response"]["type"] == "report"


@pytest.mark.asyncio
async def test_report_query_missing_site_asks_clarification():
    """测试报告生成缺少 site 时，应暂停并询问用户，而非默认站点"""
    result = await run_query("生成本周业务报告")

    assert result["intent"] == "report_generation"
    assert result["response"]["type"] == "clarification_needed"
    assert "site" in result["response"]["missing_params"]


@pytest.mark.asyncio
async def test_comparison_query():
    """测试对比分析查询"""
    result = await run_query("对比德国站和英国站的GMV")

    assert result["intent"] in ["comparison_analysis", "data_query"]


@pytest.mark.asyncio
@pytest.mark.skipif(
    not os.path.exists("data/signal.db"),
    reason="Database file not found"
)
async def test_query_with_conversation_history():
    """测试带对话历史的查询"""
    history = [
        {"role": "user", "content": "查询德国站GMV"},
        {"role": "assistant", "content": "德国站GMV为..."}
    ]

    result = await run_query(
        "那英国站呢？",
        conversation_history=history
    )

    assert "response" in result
    # 应该理解上下文，知道查询英国站GMV


@pytest.mark.asyncio
async def test_reasoning_trace():
    """测试推理轨迹完整性"""
    result = await run_query("查询美国站GMV")

    reasoning_trace = result["reasoning_trace"]

    # 至少包含 3 个节点的轨迹
    assert len(reasoning_trace) >= 3

    # 检查是否包含关键节点
    nodes = [step["node"] for step in reasoning_trace]
    assert "intent_classifier" in nodes
    assert "synthesizer" in nodes


@pytest.mark.asyncio
async def test_tool_calls_logged():
    """测试 Tool 调用是否被记录"""
    result = await run_query("查询德国站GMV", session_id="test_tool_calls")

    tool_calls = result["tool_calls"]

    # 数据查询应该至少有一个 SQL 执行
    if result["intent"] == "data_query":
        assert len(tool_calls) > 0
        assert any(call["tool"] == "execute_sql" for call in tool_calls)


@pytest.mark.asyncio
async def test_error_handling():
    """测试错误处理"""
    # 故意构造一个可能失败的查询
    result = await run_query("查询不存在的表")

    # 即使失败，也应该返回结构化的响应
    assert "response" in result
    assert "success" in result["response"]


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
