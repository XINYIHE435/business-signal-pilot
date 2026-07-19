"""
Export Utilities - 统一导出层

支持的导出格式:
- Markdown (报告和数据表格)
- PDF (从Markdown转换)
- CSV (数据导出)
"""

from typing import Dict, Any, List
from datetime import datetime
import structlog

logger = structlog.get_logger()


def generate_markdown_report(report_content: Dict[str, Any]) -> str:
    """
    生成Markdown格式的业务报告

    Args:
        report_content: 报告内容（来自report_agent_node）

    Returns:
        Markdown格式的报告文本
    """
    report_type = report_content.get("report_type", "weekly")
    start_date = report_content.get("start_date", "")
    end_date = report_content.get("end_date", "")
    exec_summary = report_content.get("executive_summary", {})

    # 标题（report_type 现支持 weekly/monthly/quarterly/custom，对应任意用户指定的时间范围）
    title_map = {"weekly": "周度业务报告", "monthly": "月度业务报告", "quarterly": "季度业务报告"}
    title = title_map.get(report_type, "业务报告")
    md = f"# {title}\n\n"
    md += f"**报告周期:** {start_date} 至 {end_date}\n\n"
    md += f"**生成时间:** {report_content.get('generated_at', datetime.now().isoformat())}\n\n"
    md += "---\n\n"

    # 1. Overall Business Performance
    md += "## 一、整体业务表现\n\n"
    md += exec_summary.get("overall_business_performance", "暂无数据") + "\n\n"

    # 2. KPI Summary
    md += "## 二、关键指标汇总\n\n"
    kpi_list = exec_summary.get("kpi_summary", [])
    if kpi_list:
        md += "| 指标名称 | 当前值 | 趋势 | 变化幅度 |\n"
        md += "|---------|--------|------|----------|\n"
        for kpi in kpi_list:
            metric_name = kpi.get("metric_name", "N/A")
            current_value = kpi.get("current_value", "N/A")
            trend = kpi.get("trend", "持平")
            change_pct = kpi.get("change_percentage", "N/A")

            # 添加趋势图标
            trend_icon = {"上升": "📈", "下降": "📉", "持平": "➡️"}.get(trend, "")
            md += f"| {metric_name} | {current_value} | {trend_icon} {trend} | {change_pct} |\n"
        md += "\n"
    else:
        md += "暂无KPI数据\n\n"

    # 3. Key Findings
    md += "## 三、关键发现\n\n"
    findings = exec_summary.get("key_findings", [])
    if findings:
        for i, finding in enumerate(findings, 1):
            md += f"{i}. {finding}\n"
        md += "\n"
    else:
        md += "暂无关键发现\n\n"

    # 4. Root Causes
    md += "## 四、根本原因分析\n\n"
    root_causes = exec_summary.get("root_causes", [])
    if root_causes:
        for i, cause in enumerate(root_causes, 1):
            cause_text = cause.get("cause", "N/A")
            confidence = cause.get("confidence", "N/A")
            evidence = cause.get("evidence", "")

            md += f"### {i}. {cause_text}\n\n"
            md += f"**置信度:** {confidence}\n\n"
            if evidence:
                md += f"**证据:** {evidence}\n\n"
        md += "\n"
    else:
        md += "暂无根本原因分析（建议进行深度诊断）\n\n"

    # 5. Recommended Actions
    md += "## 五、推荐行动\n\n"
    actions = exec_summary.get("recommended_actions", [])
    if actions:
        # 按优先级分组
        high_priority = [a for a in actions if a.get("priority") == "高"]
        medium_priority = [a for a in actions if a.get("priority") == "中"]
        low_priority = [a for a in actions if a.get("priority") == "低"]

        if high_priority:
            md += "### 🔴 高优先级\n\n"
            for action in high_priority:
                md += f"- **{action.get('action', 'N/A')}**\n"
                if action.get("expected_impact"):
                    md += f"  - 预期影响: {action['expected_impact']}\n"
            md += "\n"

        if medium_priority:
            md += "### 🟡 中优先级\n\n"
            for action in medium_priority:
                md += f"- {action.get('action', 'N/A')}\n"
                if action.get("expected_impact"):
                    md += f"  - 预期影响: {action['expected_impact']}\n"
            md += "\n"

        if low_priority:
            md += "### 🟢 低优先级\n\n"
            for action in low_priority:
                md += f"- {action.get('action', 'N/A')}\n"
            md += "\n"
    else:
        md += "暂无推荐行动\n\n"

    # 6. Next Week Focus
    md += "## 六、下周重点关注\n\n"
    focus_items = exec_summary.get("next_week_focus", [])
    if focus_items:
        for i, item in enumerate(focus_items, 1):
            md += f"{i}. {item}\n"
        md += "\n"
    else:
        md += "暂无重点关注事项\n\n"

    # 数据来源说明
    md += "---\n\n"
    md += "## 数据来源\n\n"
    data_sources = report_content.get("data_sources", {})
    if data_sources.get("reused_diagnosis"):
        md += "- 复用了根因诊断结果\n"
    if data_sources.get("reused_sql"):
        md += "- 复用了SQL查询结果\n"
    if data_sources.get("fresh_query"):
        md += "- 执行了新的数据查询\n"

    return md


def generate_diagnosis_markdown(diagnosis_report: Dict[str, Any]) -> str:
    """
    生成诊断报告的Markdown格式

    Args:
        diagnosis_report: 诊断报告内容

    Returns:
        Markdown格式的诊断报告
    """
    md = "# 根因诊断报告\n\n"
    md += f"**生成时间:** {datetime.now().isoformat()}\n\n"
    md += f"**分析模式:** {diagnosis_report.get('analysis_mode', 'N/A')}\n\n"
    md += "---\n\n"

    # 摘要
    md += "## 诊断摘要\n\n"
    md += diagnosis_report.get("summary", "暂无摘要") + "\n\n"

    # 假设
    md += "## 生成的假设\n\n"
    hypotheses = diagnosis_report.get("hypotheses", [])
    if hypotheses:
        for i, hyp in enumerate(hypotheses, 1):
            md += f"{i}. {hyp.get('description', 'N/A')} (置信度: {hyp.get('confidence', 'N/A')})\n"
        md += "\n"

    # 根本原因
    md += "## 根本原因\n\n"
    root_causes = diagnosis_report.get("root_causes", [])
    if root_causes:
        for i, cause in enumerate(root_causes, 1):
            md += f"### {i}. {cause.get('cause', 'N/A')}\n\n"
            md += f"**置信度:** {cause.get('confidence', 'N/A')}\n\n"
            if cause.get("evidence"):
                md += f"**证据:** {cause['evidence']}\n\n"
    else:
        md += "未识别出明确的根本原因\n\n"

    # 推荐行动
    md += "## 推荐行动\n\n"
    actions = diagnosis_report.get("recommended_actions", [])
    if actions:
        for i, action in enumerate(actions, 1):
            md += f"{i}. {action}\n"
    else:
        md += "暂无推荐行动\n"

    return md


def dataframe_to_csv(data: List[Dict[str, Any]]) -> str:
    """
    将数据转换为CSV格式

    Args:
        data: 数据列表（字典格式）

    Returns:
        CSV格式字符串
    """
    if not data:
        return ""

    import csv
    from io import StringIO

    output = StringIO()

    # 获取所有字段
    fieldnames = list(data[0].keys())

    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    writer.writerows(data)

    return output.getvalue()


def dataframe_to_markdown_table(data: List[Dict[str, Any]], max_rows: int = 100) -> str:
    """
    将数据转换为Markdown表格

    Args:
        data: 数据列表（字典格式）
        max_rows: 最大显示行数

    Returns:
        Markdown表格字符串
    """
    if not data:
        return "暂无数据"

    # 限制行数
    display_data = data[:max_rows]

    # 获取列名
    columns = list(display_data[0].keys())

    # 表头
    md = "| " + " | ".join(columns) + " |\n"
    md += "|" + "|".join(["---" for _ in columns]) + "|\n"

    # 数据行
    for row in display_data:
        values = [str(row.get(col, "")) for col in columns]
        md += "| " + " | ".join(values) + " |\n"

    # 如果有更多数据
    if len(data) > max_rows:
        md += f"\n*（仅显示前{max_rows}行，共{len(data)}行）*\n"

    return md


def markdown_to_pdf(markdown_content: str, output_path: str = None) -> bytes:
    """
    将Markdown转换为PDF

    渲染引擎优先级：
    1. WeasyPrint —— 排版最佳，但依赖系统级 GTK/Pango/Cairo 原生库
       （Linux/Docker/macOS 通常可用；Windows 需手动安装 GTK3 运行时）
    2. fpdf2 —— 纯 Python 后备引擎，无需系统依赖，Windows 下亦可导出中文 PDF

    Args:
        markdown_content: Markdown内容
        output_path: 输出路径（可选，如果不提供则返回bytes）

    Returns:
        PDF内容（bytes）

    Raises:
        RuntimeError: 当所有 PDF 引擎均不可用时，抛出带可读诊断信息的异常
    """
    try:
        import markdown  # noqa: F401
    except ImportError as e:
        raise RuntimeError(f"缺少 markdown 库，无法生成 PDF：{e}") from e

    # 优先尝试 WeasyPrint；其原生依赖缺失时（Windows 常见）回退到 fpdf2
    weasy_error = None
    try:
        return _markdown_to_pdf_weasyprint(markdown_content, output_path)
    except Exception as e:  # ImportError / OSError(缺少 GTK 原生库) 等
        weasy_error = e
        logger.warning("weasyprint_unavailable_fallback_fpdf", error=str(e))

    try:
        return _markdown_to_pdf_fpdf(markdown_content, output_path)
    except Exception as e:
        logger.error("pdf_generation_failed_all_engines", weasyprint_error=str(weasy_error), fpdf_error=str(e))
        raise RuntimeError(
            "PDF 生成失败：WeasyPrint 与 fpdf2 引擎均不可用。\n"
            f"- WeasyPrint: {weasy_error}\n"
            f"- fpdf2: {e}\n"
            "请安装 fpdf2（pip install fpdf2）或为 WeasyPrint 配置 GTK 运行时。"
        ) from e


def _markdown_to_pdf_weasyprint(markdown_content: str, output_path: str = None) -> bytes:
    """使用 WeasyPrint 渲染 PDF（需系统级 GTK/Pango/Cairo 原生库）"""
    import markdown
    from weasyprint import HTML, CSS
    from weasyprint.text.fonts import FontConfiguration

    # 转换Markdown为HTML
    html_content = markdown.markdown(
        markdown_content,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    # 添加CSS样式
    css_style = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: "Microsoft YaHei", "SimHei", sans-serif;
        font-size: 11pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        font-size: 24pt;
        color: #1a1a1a;
        border-bottom: 3px solid #4CAF50;
        padding-bottom: 10px;
        margin-top: 0;
    }
    h2 {
        font-size: 18pt;
        color: #2c3e50;
        border-bottom: 2px solid #ddd;
        padding-bottom: 5px;
        margin-top: 30px;
    }
    h3 {
        font-size: 14pt;
        color: #34495e;
        margin-top: 20px;
    }
    table {
        width: 100%;
        border-collapse: collapse;
        margin: 20px 0;
    }
    th, td {
        border: 1px solid #ddd;
        padding: 8px;
        text-align: left;
    }
    th {
        background-color: #4CAF50;
        color: white;
    }
    tr:nth-child(even) {
        background-color: #f9f9f9;
    }
    ul, ol {
        margin: 10px 0;
        padding-left: 30px;
    }
    strong {
        color: #2c3e50;
    }
    hr {
        border: none;
        border-top: 2px solid #eee;
        margin: 30px 0;
    }
    """

    # 完整HTML
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>{css_style}</style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    # 生成PDF
    font_config = FontConfiguration()
    pdf_bytes = HTML(string=full_html).write_pdf(
        stylesheets=[CSS(string=css_style, font_config=font_config)]
    )

    # 如果指定了输出路径，写入文件
    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

    return pdf_bytes


def _find_cjk_font() -> tuple:
    """
    查找可用的中文字体（regular, bold）

    Returns:
        (regular_path, bold_path)；bold 缺失时回退为 regular
    """
    from pathlib import Path

    # 常见中文字体候选（Windows / Linux）
    regular_candidates = [
        r"C:\Windows\Fonts\msyh.ttc",       # 微软雅黑
        r"C:\Windows\Fonts\simsun.ttc",     # 宋体
        r"C:\Windows\Fonts\simhei.ttf",     # 黑体
        "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
        "/System/Library/Fonts/PingFang.ttc",  # macOS
    ]
    bold_candidates = [
        r"C:\Windows\Fonts\msyhbd.ttc",
        r"C:\Windows\Fonts\simhei.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    ]

    regular = next((p for p in regular_candidates if Path(p).exists()), None)
    bold = next((p for p in bold_candidates if Path(p).exists()), regular)
    return regular, bold


def _replace_emojis(text: str) -> str:
    """
    将常见 emoji 替换为文本标记（供不支持 emoji 字形的字体使用）

    先做已知映射，再兜底移除其余 emoji 码点，避免 PDF 出现空白方块。
    """
    import re

    mapping = {
        "📈": "[↑]",
        "📉": "[↓]",
        "➡️": "[→]",
        "➡": "[→]",
        "🔴": "[高]",
        "🟡": "[中]",
        "🟢": "[低]",
        "✅": "[√]",
        "⚠️": "[!]",
        "⚠": "[!]",
        "📊": "",
        "🔍": "",
        "💰": "",
        "📅": "",
    }
    for emoji, repl in mapping.items():
        text = text.replace(emoji, repl)

    # 兜底：移除剩余 emoji 及变体选择符
    emoji_pattern = re.compile(
        "[\U0001F300-\U0001FAFF\U00002600-\U000027BF\U0001F000-\U0001F0FF️]",
        flags=re.UNICODE,
    )
    return emoji_pattern.sub("", text)


def _markdown_to_pdf_fpdf(markdown_content: str, output_path: str = None) -> bytes:
    """
    使用 fpdf2 渲染 PDF（纯 Python，无需系统依赖，支持中文 TTF）

    通过 markdown → HTML → fpdf2.write_html 实现，覆盖标题/表格/列表/加粗等常见结构。
    """
    import markdown
    from fpdf import FPDF

    regular_font, bold_font = _find_cjk_font()
    if not regular_font:
        raise RuntimeError("未找到可用的中文字体（msyh/simsun/simhei/Noto CJK），无法生成中文 PDF")

    # 中文字体通常不含 emoji 字形，替换为可读文本，避免 PDF 中出现空白方块
    sanitized = _replace_emojis(markdown_content)

    # 转换 Markdown → HTML
    html_content = markdown.markdown(
        sanitized,
        extensions=['tables', 'fenced_code', 'nl2br']
    )

    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    # 注册中文字体的四种样式（write_html 需要 ''/B/I/BI 全部存在）
    pdf.add_font("cjk", "", regular_font)
    pdf.add_font("cjk", "B", bold_font)
    pdf.add_font("cjk", "I", regular_font)
    pdf.add_font("cjk", "BI", bold_font)
    pdf.set_font("cjk", size=11)

    # 以中文字体为默认族渲染 HTML
    pdf.write_html(html_content, font_family="cjk")

    pdf_bytes = bytes(pdf.output())

    if output_path:
        with open(output_path, 'wb') as f:
            f.write(pdf_bytes)

    return pdf_bytes
