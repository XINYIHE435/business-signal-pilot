"""
测试 LangGraph Orchestrator
"""

import pytest
from app.agents.orchestrator import (
    simple_intent_node,
    simple_sql_node,
    synthesizer_node,
    create_simple_workflow,
    run_simple_query
)


@pytest.mark.asyncio
async def test_simple_intent_node():
    """测试意图分类节点"""
    # 测试数据查询意图
    state = {"user_query": "查询德国站的GMV"}
    result = await simple_intent_node(state)

    assert result["intent"] == "data_query"
    assert len(result["reasoning_trace"]) > 0

    # 测试诊断意图
    state = {"user_query": "为什么GMV下降了？"}
    result = await simple_intent_node(state)

    assert result["intent"] == "diagnosis"


@pytest.mark.asyncio
async def test_simple_sql_node():
    """测试 SQL 节点"""
    state = {"user_query": "查询GMV"}
    result = await simple_sql_node(state)

    assert len(result["tool_calls"]) > 0
    assert len(result["tool_results"]) > 0
    assert "sql" in result["tool_results"][0]


@pytest.mark.asyncio
async def test_synthesizer_node():
    """测试综合节点"""
    state = {
        "intent": "data_query",
        "tool_results": [{
            "sql": "SELECT 1",
            "data": [{"value": 1}]
        }]
    }

    result = await synthesizer_node(state)

    assert result["should_end"] is True
    assert "final_response" in result
    assert result["final_response"]["type"] == "data_query"


def test_create_workflow():
    """测试创建 Workflow"""
    workflow = create_simple_workflow()

    # 检查节点是否正确添加
    assert workflow is not None


@pytest.mark.asyncio
async def test_run_simple_query():
    """测试端到端查询"""
    result = await run_simple_query("查询德国站GMV", session_id="test_session")

    assert "response" in result
    assert "reasoning_trace" in result
    assert "tool_calls" in result
    assert len(result["reasoning_trace"]) > 0


@pytest.mark.asyncio
async def test_run_diagnosis_query():
    """测试诊断查询"""
    result = await run_simple_query("为什么德国站GMV下降了？", session_id="test_session")

    assert result["response"]["type"] == "diagnosis"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
