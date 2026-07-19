"""
Dashboard API 路由 V2

支持两级分类体系，同时保持向后兼容
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
import structlog

from app.core.database_v2 import db_v2
from app.models.schemas import KPIResponse, KPICard, TrendResponse, AnomalyResponse, Anomaly

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


class DashboardReportRequest(BaseModel):
    """Dashboard 报告生成请求 —— 参数视为完整可信，跳过 Parameter Validation"""
    site: str
    start_date: str
    end_date: str
    category: Optional[str] = None
    report_type: Optional[str] = None


class DashboardReportResponse(BaseModel):
    """Dashboard 报告生成响应，与 Chat 报告响应结构一致"""
    success: bool
    response: Dict[str, Any]


@router.get("/business-date")
async def get_business_date():
    """
    获取当前业务日期（数据库中的最大日期）

    Returns:
        dict: { "business_date": "2026-07-12", "description": "Latest available data date" }
    """
    try:
        business_date = db_v2.get_max_date()
        if not business_date:
            raise HTTPException(status_code=500, detail="No data available in database")

        return {
            "business_date": str(business_date),
            "description": "Latest available data date"
        }
    except Exception as e:
        logger.error("business_date_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch business date: {str(e)}")


def build_category_filter(category: Optional[str], db_instance) -> str:
    """
    构建分类过滤条件（兼容 V1 和 V2 Schema）

    Args:
        category: 用户查询的分类名称
        db_instance: 数据库实例

    Returns:
        SQL WHERE 子句
    """
    if not category:
        return ""

    if not db_instance.is_v2_schema():
        # V1: 单级分类
        return f" AND category = '{category}'"

    # V2: 两级分类，智能匹配
    mapping = db_instance.get_category_mapping(category)

    if mapping.get('where_clause'):
        return f" AND {mapping['where_clause']}"

    return ""


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    site: str = Query("US", description="站点代码 (US, DE, UK, etc.)"),
    category: Optional[str] = Query(None, description="品类（可选，支持 L1 或 L2）"),
    days: int = Query(7, description="对比天数", ge=1, le=365)
):
    """
    获取 Dashboard KPI 数据

    返回当前周期和上一周期的对比数据

    **兼容性**:
    - V1 Schema: 使用 `category` 字段
    - V2 Schema: 自动匹配 `category_l1` 或 `category_l2`
    """

    try:
        # 获取数据库中的最大业务日期
        end_date = db_v2.get_max_date()
        if not end_date:
            raise HTTPException(status_code=500, detail="No data available in database")

        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)
        prev_end_date = start_date - timedelta(days=1)

        # 构建查询
        where_clause = f"site = '{site}'"
        where_clause += build_category_filter(category, db_v2)

        # 查询当前周期数据
        current_query = f"""
            SELECT
                SUM(gmv) as total_gmv,
                SUM(sold_items) as total_si,
                AVG(ctr) as avg_ctr,
                AVG(cvr) as avg_cvr,
                SUM(gmv) / NULLIF(SUM(sold_items), 0) as avg_asp
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{start_date}'
              AND date <= '{end_date}'
        """

        current_result = db_v2.execute(current_query)
        current_data = current_result[0] if current_result else (0, 0, 0, 0, 0)

        # 查询上一周期数据
        prev_query = f"""
            SELECT
                SUM(gmv) as total_gmv,
                SUM(sold_items) as total_si,
                AVG(ctr) as avg_ctr,
                AVG(cvr) as avg_cvr,
                SUM(gmv) / NULLIF(SUM(sold_items), 0) as avg_asp
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{prev_start_date}'
              AND date < '{start_date}'
        """

        prev_result = db_v2.execute(prev_query)
        prev_data = prev_result[0] if prev_result else (0, 0, 0, 0, 0)

        # 计算变化百分比
        def calc_change(current, previous):
            if previous == 0 or previous is None:
                return 0.0
            return ((current - previous) / previous) * 100

        # 构建 KPI 卡片
        kpis = [
            KPICard(
                name="GMV",
                value=float(current_data[0] or 0),
                change_percent=calc_change(current_data[0], prev_data[0]),
                trend="up" if calc_change(current_data[0], prev_data[0]) >= 0 else "down",
                formatted_value=f"${current_data[0]:,.2f}" if current_data[0] else "$0.00"
            ),
            KPICard(
                name="SI",
                value=float(current_data[1] or 0),
                change_percent=calc_change(current_data[1], prev_data[1]),
                trend="up" if calc_change(current_data[1], prev_data[1]) >= 0 else "down",
                formatted_value=f"{int(current_data[1] or 0):,}"
            ),
            KPICard(
                name="CTR",
                value=float(current_data[2] or 0),
                change_percent=calc_change(current_data[2], prev_data[2]),
                trend="up" if calc_change(current_data[2], prev_data[2]) >= 0 else "down",
                formatted_value=f"{(current_data[2] or 0) * 100:.2f}%"
            ),
            KPICard(
                name="CVR",
                value=float(current_data[3] or 0),
                change_percent=calc_change(current_data[3], prev_data[3]),
                trend="up" if calc_change(current_data[3], prev_data[3]) >= 0 else "down",
                formatted_value=f"{(current_data[3] or 0) * 100:.2f}%"
            ),
            KPICard(
                name="ASP",
                value=float(current_data[4] or 0),
                change_percent=calc_change(current_data[4], prev_data[4]),
                trend="up" if calc_change(current_data[4], prev_data[4]) >= 0 else "down",
                formatted_value=f"${current_data[4]:.2f}" if current_data[4] else "$0.00"
            ),
        ]

        logger.info(
            "kpis_fetched",
            site=site,
            category=category,
            days=days,
            gmv=current_data[0],
            schema_version=db_v2._schema_version
        )

        return KPIResponse(
            kpis=kpis,
            site=site,
            category=category,
            date_range=f"{start_date} to {end_date}"
        )

    except Exception as e:
        logger.error("kpis_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch KPIs: {str(e)}")


@router.get("/trends", response_model=TrendResponse)
async def get_trends(
    site: str = Query("US", description="站点代码"),
    category: Optional[str] = Query(None, description="品类（可选，支持 L1 或 L2）"),
    days: int = Query(30, description="天数", ge=7, le=730)
):
    """
    获取趋势数据

    **兼容性**: 自动适配 V1/V2 Schema
    """

    try:
        # 获取数据库中的最大业务日期
        end_date = db_v2.get_max_date()
        if not end_date:
            raise HTTPException(status_code=500, detail="No data available in database")

        start_date = end_date - timedelta(days=days)

        where_clause = f"site = '{site}'"
        where_clause += build_category_filter(category, db_v2)

        query = f"""
            SELECT
                date,
                SUM(gmv) as gmv,
                SUM(sold_items) as si,
                AVG(ctr) as ctr,
                AVG(cvr) as cvr,
                SUM(gmv) / NULLIF(SUM(sold_items), 0) as asp,
                SUM(sold_items) / NULLIF(SUM(live_listings), 0) as str_rate
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{start_date}'
              AND date <= '{end_date}'
            GROUP BY date
            ORDER BY date
        """

        results = db_v2.execute(query)

        dates = []
        gmv = []
        sold_items = []
        ctr = []
        cvr = []
        asp = []
        str_rate = []

        for row in results:
            dates.append(str(row[0]))
            gmv.append(float(row[1] or 0))
            sold_items.append(int(row[2] or 0))
            ctr.append(float(row[3] or 0))
            cvr.append(float(row[4] or 0))
            asp.append(float(row[5] or 0))
            str_rate.append(float(row[6] or 0))

        logger.info(
            "trends_fetched",
            site=site,
            category=category,
            days=days,
            data_points=len(dates)
        )

        return TrendResponse(
            dates=dates,
            gmv=gmv,
            sold_items=sold_items,
            ctr=ctr,
            cvr=cvr,
            asp=asp,
            str_rate=str_rate
        )

    except Exception as e:
        logger.error("trends_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")


@router.get("/anomalies", response_model=AnomalyResponse)
async def get_anomalies(
    site: Optional[str] = Query(None, description="站点代码（可选）"),
    days: int = Query(7, description="天数", ge=1, le=365),
    threshold: float = Query(0.15, description="异常阈值", ge=0.05, le=0.5)
):
    """
    获取异常数据

    **兼容性**: 自动适配 V1/V2 Schema
    """

    try:
        # 获取数据库中的最大业务日期
        end_date = db_v2.get_max_date()
        if not end_date:
            raise HTTPException(status_code=500, detail="No data available in database")

        start_date = end_date - timedelta(days=days)

        where_clause = "1=1"
        if site:
            where_clause += f" AND site = '{site}'"

        # 简单异常检测：GMV 环比变化超过阈值
        if not db_v2.is_v2_schema():
            # V1 Schema
            category_field = "category"
        else:
            # V2 Schema
            category_field = "category_l2"

        query = f"""
            WITH current_period AS (
                SELECT
                    date,
                    site,
                    {category_field} as category,
                    gmv,
                    LAG(gmv) OVER (PARTITION BY site, {category_field} ORDER BY date) as prev_gmv
                FROM daily_metrics
                WHERE {where_clause}
                  AND date >= '{start_date}'
                  AND date <= '{end_date}'
            )
            SELECT
                date,
                site,
                category,
                prev_gmv as expected_value,
                gmv as actual_value,
                CASE
                    WHEN prev_gmv > 0 THEN ((gmv - prev_gmv) / prev_gmv)
                    ELSE 0
                END as deviation
            FROM current_period
            WHERE prev_gmv > 0
              AND ABS((gmv - prev_gmv) / prev_gmv) > {threshold}
            ORDER BY ABS((gmv - prev_gmv) / prev_gmv) DESC
            LIMIT 50
        """

        results = db_v2.execute(query)

        anomalies = []
        for row in results:
            deviation = float(row[5])
            severity = "critical" if abs(deviation) > 0.3 else "high" if abs(deviation) > 0.2 else "medium"

            anomalies.append(Anomaly(
                date=str(row[0]),
                metric="GMV",
                site=row[1],
                category=row[2],
                expected_value=float(row[3] or 0),
                actual_value=float(row[4] or 0),
                deviation_percent=deviation * 100,
                severity=severity
            ))

        logger.info(
            "anomalies_fetched",
            site=site,
            days=days,
            threshold=threshold,
            count=len(anomalies)
        )

        return AnomalyResponse(
            anomalies=anomalies,
            total_count=len(anomalies)
        )

    except Exception as e:
        logger.error("anomalies_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch anomalies: {str(e)}")


@router.post("/report", response_model=DashboardReportResponse)
async def generate_dashboard_report(request: DashboardReportRequest):
    """
    Dashboard 报告生成入口

    与 Chat 报告生成（/api/v1/chat/query，intent=report_generation）共用同一套
    ReportRequest 结构和 Report Agent 逻辑（见 orchestrator_v2.run_dashboard_report），
    唯一区别：Dashboard 传入的 site/start_date/end_date 视为完整可信参数，
    直接跳过 Parameter Validation，不会触发澄清询问。
    """
    from app.agents.orchestrator_v2 import run_dashboard_report

    try:
        result = await run_dashboard_report(
            site=request.site,
            start_date=request.start_date,
            end_date=request.end_date,
            category=request.category or "",
            report_type=request.report_type,
        )
        return DashboardReportResponse(
            success=result["response"].get("success", False),
            response=result["response"],
        )
    except Exception as e:
        logger.error("dashboard_report_endpoint_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Report generation failed: {str(e)}")
