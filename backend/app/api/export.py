"""
Export API - 导出接口

支持:
- 报告导出（Markdown/PDF）
- 查询结果导出（CSV/Markdown Table）
- 诊断分析导出（Markdown/PDF）
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime
import structlog

from app.utils.export import (
    generate_markdown_report,
    generate_diagnosis_markdown,
    dataframe_to_csv,
    dataframe_to_markdown_table,
    markdown_to_pdf
)

logger = structlog.get_logger()
router = APIRouter(prefix="/api/v1/export", tags=["export"])


# === Request/Response Models ===

class ExportReportRequest(BaseModel):
    """报告导出请求"""
    report_content: Dict[str, Any]
    format: Literal["markdown", "pdf"] = "markdown"


class ExportQueryResultRequest(BaseModel):
    """查询结果导出请求"""
    data: List[Dict[str, Any]]
    format: Literal["csv", "markdown"] = "csv"
    filename: Optional[str] = None


class ExportDiagnosisRequest(BaseModel):
    """诊断报告导出请求"""
    diagnosis_report: Dict[str, Any]
    format: Literal["markdown", "pdf"] = "markdown"


# === Endpoints ===

@router.post("/report")
async def export_report(request: ExportReportRequest):
    """
    导出业务报告

    支持格式:
    - markdown: 返回文本内容
    - pdf: 返回PDF文件（二进制）
    """
    try:
        logger.info(
            "exporting_report",
            format=request.format,
            report_type=request.report_content.get("report_type")
        )

        # 生成Markdown
        markdown_content = generate_markdown_report(request.report_content)

        if request.format == "markdown":
            # 返回Markdown文本
            return Response(
                content=markdown_content,
                media_type="text/markdown; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="business_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md"'
                }
            )

        elif request.format == "pdf":
            # 转换为PDF
            try:
                pdf_bytes = markdown_to_pdf(markdown_content)
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="business_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                    }
                )
            except Exception as e:
                logger.error("pdf_generation_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("report_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"报告导出失败: {str(e)}")


@router.post("/query-result")
async def export_query_result(request: ExportQueryResultRequest):
    """
    导出查询结果

    支持格式:
    - csv: 返回CSV文件
    - markdown: 返回Markdown表格
    """
    try:
        logger.info(
            "exporting_query_result",
            format=request.format,
            row_count=len(request.data)
        )

        if not request.data:
            raise HTTPException(status_code=400, detail="数据为空，无法导出")

        filename = request.filename or f"query_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        if request.format == "csv":
            csv_content = dataframe_to_csv(request.data)
            return Response(
                content=csv_content,
                media_type="text/csv; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.csv"'
                }
            )

        elif request.format == "markdown":
            md_table = dataframe_to_markdown_table(request.data)
            return Response(
                content=md_table,
                media_type="text/markdown; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}.md"'
                }
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error("query_result_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"查询结果导出失败: {str(e)}")


@router.post("/diagnosis")
async def export_diagnosis(request: ExportDiagnosisRequest):
    """
    导出诊断报告

    支持格式:
    - markdown: 返回文本内容
    - pdf: 返回PDF文件
    """
    try:
        logger.info(
            "exporting_diagnosis",
            format=request.format,
            analysis_mode=request.diagnosis_report.get("analysis_mode")
        )

        # 生成Markdown
        markdown_content = generate_diagnosis_markdown(request.diagnosis_report)

        if request.format == "markdown":
            return Response(
                content=markdown_content,
                media_type="text/markdown; charset=utf-8",
                headers={
                    "Content-Disposition": f'attachment; filename="diagnosis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.md"'
                }
            )

        elif request.format == "pdf":
            try:
                pdf_bytes = markdown_to_pdf(markdown_content)
                return Response(
                    content=pdf_bytes,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f'attachment; filename="diagnosis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf"'
                    }
                )
            except Exception as e:
                logger.error("pdf_generation_failed", error=str(e))
                raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")

    except HTTPException:
        raise
    except Exception as e:
        logger.error("diagnosis_export_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"诊断报告导出失败: {str(e)}")


@router.get("/health")
async def export_health():
    """健康检查"""
    # markdown 是 PDF 转换的基础依赖
    markdown_ok = False
    try:
        import markdown  # noqa: F401
        markdown_ok = True
    except ImportError:
        pass

    # 检测可用的 PDF 引擎（任一可用即支持 PDF）
    # 注意：weasyprint 在缺少 GTK 原生库时抛 OSError，故用宽泛异常捕获
    engines = []
    try:
        import weasyprint  # noqa: F401
        engines.append("weasyprint")
    except Exception:
        pass
    try:
        import fpdf  # noqa: F401
        engines.append("fpdf2")
    except Exception:
        pass

    pdf_available = markdown_ok and bool(engines)

    return {
        "status": "healthy",
        "pdf_export_available": pdf_available,
        "pdf_engines": engines,
        "supported_formats": {
            "report": ["markdown", "pdf"] if pdf_available else ["markdown"],
            "query_result": ["csv", "markdown"],
            "diagnosis": ["markdown", "pdf"] if pdf_available else ["markdown"]
        }
    }
