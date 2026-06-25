"""
Dashboard API 路由

提供业务监控相关的 API 端点：
- KPI 数据
- 趋势数据
- 异常检测
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from datetime import datetime, timedelta
import structlog

from app.core.database import db
from app.models.schemas import KPIResponse, KPICard, TrendResponse, AnomalyResponse, Anomaly

logger = structlog.get_logger()

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])


@router.get("/kpis", response_model=KPIResponse)
async def get_kpis(
    site: str = Query("US", description="站点代码 (US, DE, UK, etc.)"),
    category: Optional[str] = Query(None, description="品类（可选）"),
    days: int = Query(7, description="对比天数", ge=1, le=90)
):
    """
    获取 Dashboard KPI 数据

    返回当前周期和上一周期的对比数据
    """

    try:
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        prev_start_date = start_date - timedelta(days=days)
        prev_end_date = start_date - timedelta(days=1)

        # 构建查询
        where_clause = f"site = '{site}'"
        if category:
            where_clause += f" AND category = '{category}'"

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

        current_result = db.execute(current_query)
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

        prev_result = db.execute(prev_query)
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
            gmv=current_data[0]
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
    category: Optional[str] = Query(None, description="品类（可选）"),
    days: int = Query(30, description="天数", ge=7, le=90)
):
    """
    获取趋势数据

    返回指定天数内的每日指标趋势
    """

    try:
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)

        # 构建查询
        where_clause = f"site = '{site}'"
        if category:
            where_clause += f" AND category = '{category}'"

        query = f"""
            SELECT
                date,
                SUM(gmv) as daily_gmv,
                SUM(sold_items) as daily_si,
                AVG(ctr) as daily_ctr,
                AVG(cvr) as daily_cvr
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{start_date}'
              AND date <= '{end_date}'
            GROUP BY date
            ORDER BY date ASC
        """

        results = db.execute(query)

        # 构建响应数据
        dates = []
        gmv = []
        sold_items = []
        ctr = []
        cvr = []

        for row in results:
            dates.append(str(row[0]))
            gmv.append(float(row[1] or 0))
            sold_items.append(int(row[2] or 0))
            ctr.append(float(row[3] or 0))
            cvr.append(float(row[4] or 0))

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
            cvr=cvr
        )

    except Exception as e:
        logger.error("trends_fetch_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")


@router.get("/anomalies", response_model=AnomalyResponse)
async def get_anomalies(
    site: Optional[str] = Query(None, description="站点代码（可选）"),
    days: int = Query(7, description="检测天数", ge=1, le=30),
    threshold: float = Query(0.15, description="异常阈值（默认15%）", ge=0.05, le=0.50)
):
    """
    检测异常指标

    使用简单的统计方法检测异常：
    - 计算每个指标的历史平均值
    - 标记偏离超过阈值的数据点
    """

    try:
        # 计算日期范围
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        baseline_start = start_date - timedelta(days=30)  # 使用前30天作为基线

        # 构建 WHERE 子句
        where_clause = "1=1"
        if site:
            where_clause = f"site = '{site}'"

        # 查询基线数据（计算历史平均值）
        baseline_query = f"""
            SELECT
                site,
                category,
                AVG(gmv) as avg_gmv,
                AVG(ctr) as avg_ctr,
                AVG(cvr) as avg_cvr
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{baseline_start}'
              AND date < '{start_date}'
            GROUP BY site, category
        """

        baseline_results = db.execute(baseline_query)

        # 构建基线字典
        baselines = {}
        for row in baseline_results:
            key = (row[0], row[1])  # (site, category)
            baselines[key] = {
                'avg_gmv': float(row[2] or 0),
                'avg_ctr': float(row[3] or 0),
                'avg_cvr': float(row[4] or 0)
            }

        # 查询最近数据
        recent_query = f"""
            SELECT
                date,
                site,
                category,
                SUM(gmv) as gmv,
                AVG(ctr) as ctr,
                AVG(cvr) as cvr
            FROM daily_metrics
            WHERE {where_clause}
              AND date >= '{start_date}'
              AND date <= '{end_date}'
            GROUP BY date, site, category
            ORDER BY date DESC
        """

        recent_results = db.execute(recent_query)

        # 检测异常
        anomalies = []

        for row in recent_results:
            date_str = str(row[0])
            site_val = row[1]
            category_val = row[2]
            gmv_val = float(row[3] or 0)
            ctr_val = float(row[4] or 0)
            cvr_val = float(row[5] or 0)

            key = (site_val, category_val)

            if key not in baselines:
                continue

            baseline = baselines[key]

            # 检查 GMV 异常
            if baseline['avg_gmv'] > 0:
                gmv_deviation = (gmv_val - baseline['avg_gmv']) / baseline['avg_gmv']
                if abs(gmv_deviation) > threshold:
                    severity = "critical" if abs(gmv_deviation) > 0.3 else "high" if abs(gmv_deviation) > 0.2 else "medium"
                    anomalies.append(Anomaly(
                        date=date_str,
                        metric="gmv",
                        site=site_val,
                        category=category_val,
                        expected_value=baseline['avg_gmv'],
                        actual_value=gmv_val,
                        deviation_percent=gmv_deviation * 100,
                        severity=severity
                    ))

            # 检查 CTR 异常
            if baseline['avg_ctr'] > 0:
                ctr_deviation = (ctr_val - baseline['avg_ctr']) / baseline['avg_ctr']
                if abs(ctr_deviation) > threshold:
                    severity = "high" if abs(ctr_deviation) > 0.25 else "medium"
                    anomalies.append(Anomaly(
                        date=date_str,
                        metric="ctr",
                        site=site_val,
                        category=category_val,
                        expected_value=baseline['avg_ctr'],
                        actual_value=ctr_val,
                        deviation_percent=ctr_deviation * 100,
                        severity=severity
                    ))

            # 检查 CVR 异常
            if baseline['avg_cvr'] > 0:
                cvr_deviation = (cvr_val - baseline['avg_cvr']) / baseline['avg_cvr']
                if abs(cvr_deviation) > threshold:
                    severity = "high" if abs(cvr_deviation) > 0.25 else "medium"
                    anomalies.append(Anomaly(
                        date=date_str,
                        metric="cvr",
                        site=site_val,
                        category=category_val,
                        expected_value=baseline['avg_cvr'],
                        actual_value=cvr_val,
                        deviation_percent=cvr_deviation * 100,
                        severity=severity
                    ))

        # 按严重程度和日期排序
        anomalies.sort(key=lambda x: (
            {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(x.severity, 4),
            x.date
        ), reverse=True)

        # 限制返回数量
        anomalies = anomalies[:50]

        logger.info(
            "anomalies_detected",
            site=site,
            days=days,
            threshold=threshold,
            anomaly_count=len(anomalies)
        )

        return AnomalyResponse(
            anomalies=anomalies,
            total_count=len(anomalies)
        )

    except Exception as e:
        logger.error("anomaly_detection_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to detect anomalies: {str(e)}")
