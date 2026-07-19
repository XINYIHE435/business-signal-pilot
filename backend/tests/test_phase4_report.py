"""
测试 Phase 4: Report Agent 和 Export 功能
"""

import pytest
from app.agents.orchestrator_v2 import run_query


@pytest.mark.asyncio
async def test_report_generation_intent():
    """测试报告生成意图识别和执行（site + 时间范围均已指定）"""

    # 测试周报生成
    result = await run_query(
        query="生成德国站本周业务报告",
        session_id="test-report-weekly"
    )

    assert result is not None
    assert "response" in result
    assert result["intent"] == "report_generation"

    response = result["response"]
    assert response["type"] == "report"

    # 如果成功，应该有report相关字段
    if response.get("success"):
        assert "executive_summary" in response
        assert "report_type" in response


@pytest.mark.asyncio
async def test_report_generation_monthly():
    """测试月报生成"""

    result = await run_query(
        query="导出德国站本月业务月报",
        session_id="test-report-monthly"
    )

    assert result is not None
    assert result["intent"] == "report_generation"

    # 检查entities是否正确提取report_type（可能在entities中，也可能由默认值决定）
    assert "entities" in result


@pytest.mark.asyncio
async def test_report_generation_missing_params_then_clarify():
    """
    测试 Parameter Validation：缺少必要参数（site/date_range）时应暂停并询问用户，
    而不是默认生成"过去一周/过去一个月"报告；用户补充参数后应基于用户指定的
    真实筛选条件继续生成报告。
    """
    # Round 1：缺少时间范围，应暂停询问，而非默认给"最近一周"
    result = await run_query(
        query="生成德国站业务报告",
        session_id="test-report-clarify"
    )
    assert result["intent"] == "report_generation"
    response = result["response"]
    assert response["type"] == "clarification_needed"
    assert "date_range" in response["missing_params"]
    assert response.get("question")

    # Round 2：用户补充时间范围，应沿用同一个 site，并严格使用指定的时间范围查询
    history = [
        {"role": "user", "content": "生成德国站业务报告"},
        {"role": "assistant", "content": response["question"]},
    ]
    result2 = await run_query(
        query="2025年7月",
        session_id="test-report-clarify",
        conversation_history=history,
    )
    response2 = result2["response"]
    assert response2["type"] == "report"
    assert response2.get("start_date") == "2025-07-01"
    assert response2.get("end_date") == "2025-07-31"


@pytest.mark.asyncio
async def test_report_generation_absolute_quarter():
    """测试绝对时间范围解析：YYYY年QN 应严格解析为对应季度，而不是默认窗口"""
    result = await run_query(
        query="生成德国站2025年Q1业务报告",
        session_id="test-report-q1"
    )
    response = result["response"]
    assert response["type"] == "report"
    assert response.get("start_date") == "2025-01-01"
    assert response.get("end_date") == "2025-03-31"


def test_export_utilities():
    """测试导出工具函数"""
    from app.utils.export import (
        dataframe_to_csv,
        dataframe_to_markdown_table,
        generate_markdown_report
    )

    # 测试数据
    test_data = [
        {"site": "DE", "gmv": 100000, "date": "2024-01-01"},
        {"site": "US", "gmv": 150000, "date": "2024-01-01"},
    ]

    # 测试CSV导出
    csv_output = dataframe_to_csv(test_data)
    assert "site,gmv,date" in csv_output
    assert "DE,100000" in csv_output

    # 测试Markdown表格导出
    md_output = dataframe_to_markdown_table(test_data)
    assert "| site | gmv | date |" in md_output
    assert "| DE | 100000 |" in md_output

    # 测试报告生成
    report_content = {
        "report_type": "weekly",
        "start_date": "2024-01-01",
        "end_date": "2024-01-07",
        "executive_summary": {
            "overall_business_performance": "整体表现良好",
            "kpi_summary": [
                {
                    "metric_name": "GMV",
                    "current_value": "100万",
                    "trend": "上升",
                    "change_percentage": "+10%"
                }
            ],
            "key_findings": ["发现1", "发现2"],
            "root_causes": [
                {
                    "cause": "原因1",
                    "confidence": "高",
                    "evidence": "证据1"
                }
            ],
            "recommended_actions": [
                {
                    "action": "行动1",
                    "priority": "高",
                    "expected_impact": "提升GMV"
                }
            ],
            "next_week_focus": ["重点1", "重点2"]
        },
        "generated_at": "2024-01-07T12:00:00",
        "data_sources": {
            "reused_diagnosis": False,
            "reused_sql": True,
            "fresh_query": False
        }
    }

    markdown = generate_markdown_report(report_content)
    assert "周度业务报告" in markdown
    assert "整体业务表现" in markdown
    assert "关键指标汇总" in markdown
    assert "GMV" in markdown
    assert "上升" in markdown


def test_pdf_export():
    """
    测试PDF导出完整链路

    markdown_to_pdf 会优先尝试 WeasyPrint，缺少系统级 GTK 原生库时
    自动回退到纯 Python 的 fpdf2 引擎，保证任意环境都能生成 PDF。
    """
    from app.utils.export import markdown_to_pdf

    # 含中文与表格，验证中文字体与表格渲染
    md = (
        "# 周度业务报告\n\n"
        "## 关键指标汇总\n\n"
        "| 指标 | 当前值 | 趋势 |\n"
        "|---|---|---|\n"
        "| GMV | $307,345,596 | 上升 |\n\n"
        "## 关键发现\n\n"
        "1. GMV增长8.5%\n"
    )

    pdf_bytes = markdown_to_pdf(md)
    assert len(pdf_bytes) > 0
    assert pdf_bytes[:5] == b'%PDF-'  # 有效 PDF 文件头


def test_pdf_export_via_api():
    """测试 PDF 导出的 HTTP 端点（复现并验证 500 修复）"""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app)

    # 健康检查应报告至少一个可用 PDF 引擎
    health = client.get("/api/v1/export/health").json()
    assert health["pdf_export_available"] is True
    assert len(health.get("pdf_engines", [])) >= 1

    payload = {
        "report_content": {
            "report_type": "weekly",
            "start_date": "2026-07-06",
            "end_date": "2026-07-12",
            "executive_summary": {
                "overall_business_performance": "DE站GMV增长8.5%。",
                "kpi_summary": [
                    {"metric_name": "GMV", "current_value": "$307M",
                     "trend": "上升", "change_percentage": "+8.5%"}
                ],
                "key_findings": ["GMV增长8.5%"],
                "root_causes": [{"cause": "客单价提升", "confidence": "高", "evidence": "ASP+8.2%"}],
                "recommended_actions": [{"action": "扩大推广", "priority": "高", "expected_impact": "+5%"}],
                "next_week_focus": ["跟踪客单价"],
            },
        },
        "format": "pdf",
    }

    resp = client.post("/api/v1/export/report", json=payload)
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/pdf"
    assert resp.content[:5] == b'%PDF-'


if __name__ == "__main__":
    import asyncio

    # 运行异步测试
    print("Testing report generation...")
    asyncio.run(test_report_generation_intent())
    print("✓ Report generation test passed")

    print("\nTesting export utilities...")
    test_export_utilities()
    print("✓ Export utilities test passed")

    print("\nAll tests passed!")
