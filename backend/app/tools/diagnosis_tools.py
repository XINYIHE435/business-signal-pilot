"""
Diagnosis Tools - 诊断 Agent 专用工具层

统一继承现有 BaseTool 接口（见 registry.py），便于后续替换为真实 API 或 MCP。

工具分两类：
1. DuckDB 真实表查询：CampaignTool / InventoryTool / SellerTool
2. JSON Mock 数据：HolidayTool / PolicyTool / NewsTool

所有 Tool 通过 register_diagnosis_tools() 注册进全局 tool_registry。
"""

from typing import Any, Dict, List, Optional
from pathlib import Path
import json
import structlog

from app.tools.registry import BaseTool, tool_registry
from app.adapters.database.base import DatabaseAdapter

logger = structlog.get_logger()

# Mock 数据目录
_MOCK_DIR = Path(__file__).parent / "mock_data"


def _load_json(filename: str) -> Dict[str, Any]:
    """加载 mock JSON 文件"""
    path = _MOCK_DIR / filename
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error("mock_data_load_failed", file=filename, error=str(e))
        return {}


# ============================================================
# DuckDB 真实表查询工具
# ============================================================

class CampaignTool(BaseTool):
    """营销活动查询工具（campaigns 表）"""

    name = "query_campaigns"
    description = "Query marketing campaigns active for a site/category/date range to check campaign-driven GMV effects"

    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string", "description": "Site code (US, DE, UK, ...)"},
                    "category_l1": {"type": "string", "description": "Optional L1 category name"},
                    "start_date": {"type": "string", "description": "Range start (YYYY-MM-DD)"},
                    "end_date": {"type": "string", "description": "Range end (YYYY-MM-DD)"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: str,
        category_l1: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        where = [f"site = '{site}'"]
        if category_l1:
            where.append(f"(category_l1 = '{category_l1}' OR category_l1 IS NULL)")
        if start_date and end_date:
            # 活动与查询区间有重叠
            where.append(f"start_date <= '{end_date}' AND end_date >= '{start_date}'")
        where_clause = " AND ".join(where)

        sql = f"""
            SELECT campaign_id, campaign_name, site, category_l1, category_l2,
                   start_date, end_date, discount_rate, subsidy_budget,
                   target_gmv, actual_gmv, roi
            FROM campaigns
            WHERE {where_clause}
            ORDER BY start_date DESC
            LIMIT 20
        """
        try:
            rows = await self.adapter.execute(sql)
            return {
                "success": True,
                "tool": self.name,
                "hypothesis_type": "campaign",
                "row_count": len(rows),
                "data": _clean_rows(rows),
            }
        except Exception as e:
            logger.error("campaign_tool_failed", error=str(e))
            return {"success": False, "tool": self.name, "error": str(e)}


class InventoryTool(BaseTool):
    """库存健康查询工具（inventory_daily 表）"""

    name = "query_inventory"
    description = "Query daily inventory health (stock-outs, days of supply) for a site/category to check inventory-driven effects"

    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "category_l1": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: str,
        category_l1: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        where = [f"site = '{site}'"]
        if category_l1:
            where.append(f"category_l1 = '{category_l1}'")
        if start_date and end_date:
            where.append(f"date >= '{start_date}' AND date <= '{end_date}'")
        where_clause = " AND ".join(where)

        # 聚合到日级别，观察缺货率与供应天数趋势
        sql = f"""
            SELECT date,
                   AVG(out_of_stock_rate) AS avg_oos_rate,
                   AVG(days_of_supply) AS avg_days_of_supply,
                   SUM(live_listings) AS total_live_listings,
                   SUM(restock_qty) AS total_restock
            FROM inventory_daily
            WHERE {where_clause}
            GROUP BY date
            ORDER BY date DESC
            LIMIT 30
        """
        try:
            rows = await self.adapter.execute(sql)
            return {
                "success": True,
                "tool": self.name,
                "hypothesis_type": "inventory",
                "row_count": len(rows),
                "data": _clean_rows(rows),
            }
        except Exception as e:
            logger.error("inventory_tool_failed", error=str(e))
            return {"success": False, "tool": self.name, "error": str(e)}


class SellerTool(BaseTool):
    """卖家表现查询工具（seller_daily_metrics 表）"""

    name = "query_sellers"
    description = "Query top-seller GMV, share and rank for a site/category to check seller-driven effects (churn, share shifts)"

    def __init__(self, adapter: DatabaseAdapter):
        self.adapter = adapter

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "category_l1": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: str,
        category_l1: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        where = [f"site = '{site}'"]
        if category_l1:
            where.append(f"category_l1 = '{category_l1}'")
        if start_date and end_date:
            where.append(f"date >= '{start_date}' AND date <= '{end_date}'")
        where_clause = " AND ".join(where)

        # 期间内 Top 卖家 GMV 与平均份额
        sql = f"""
            SELECT seller_id, seller_name,
                   SUM(gmv) AS total_gmv,
                   AVG(seller_share) AS avg_share,
                   AVG(seller_rank) AS avg_rank
            FROM seller_daily_metrics
            WHERE {where_clause}
            GROUP BY seller_id, seller_name
            ORDER BY total_gmv DESC
            LIMIT 10
        """
        try:
            rows = await self.adapter.execute(sql)
            return {
                "success": True,
                "tool": self.name,
                "hypothesis_type": "seller",
                "row_count": len(rows),
                "data": _clean_rows(rows),
            }
        except Exception as e:
            logger.error("seller_tool_failed", error=str(e))
            return {"success": False, "tool": self.name, "error": str(e)}


# ============================================================
# JSON Mock 数据工具
# ============================================================

def _filter_by_site(items: List[Dict], site: Optional[str]) -> List[Dict]:
    """按站点过滤（ALL 视为匹配任意站点）"""
    if not site:
        return items
    return [it for it in items if it.get("site") in (site, "ALL", None)]


def _overlaps(item_start: str, item_end: str, start: Optional[str], end: Optional[str]) -> bool:
    """判断日期区间是否重叠（字符串 YYYY-MM-DD 可直接比较）"""
    if not start or not end:
        return True
    return item_start <= end and item_end >= start


class HolidayTool(BaseTool):
    """节假日查询工具（JSON mock）"""

    name = "query_holidays"
    description = "Look up holidays/seasonal events affecting a site within a date range (holiday hypothesis)"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        data = _load_json("holidays.json").get("holidays", [])
        matched = [
            h for h in _filter_by_site(data, site)
            if _overlaps(h.get("start_date", ""), h.get("end_date", ""), start_date, end_date)
        ]
        return {
            "success": True,
            "tool": self.name,
            "hypothesis_type": "holiday",
            "row_count": len(matched),
            "data": matched,
        }


class PolicyTool(BaseTool):
    """平台政策查询工具（JSON mock）"""

    name = "query_policies"
    description = "Look up platform policy changes affecting a site/category around a date range (policy hypothesis)"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "category_l1": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: Optional[str] = None,
        category_l1: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        data = _load_json("policies.json").get("policies", [])
        matched = []
        for p in _filter_by_site(data, site):
            # 政策生效日落在区间内（或未提供区间）
            eff = p.get("effective_date", "")
            in_range = True
            if start_date and end_date:
                in_range = start_date <= eff <= end_date
            # 品类匹配（None 表示全站政策）
            cat_ok = (not category_l1) or p.get("category_l1") in (category_l1, None)
            if in_range and cat_ok:
                matched.append(p)
        return {
            "success": True,
            "tool": self.name,
            "hypothesis_type": "policy",
            "row_count": len(matched),
            "data": matched,
        }


class NewsTool(BaseTool):
    """市场/竞争新闻查询工具（JSON mock）"""

    name = "query_news"
    description = "Look up market/competition news for a site/category within a date range (competition hypothesis)"

    def get_schema(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    "site": {"type": "string"},
                    "category_l1": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["site"],
            },
        }

    async def execute(
        self,
        site: Optional[str] = None,
        category_l1: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        data = _load_json("news.json").get("news", [])
        matched = []
        for n in _filter_by_site(data, site):
            d = n.get("date", "")
            in_range = True
            if start_date and end_date:
                in_range = start_date <= d <= end_date
            cat_ok = (not category_l1) or n.get("category_l1") in (category_l1, None)
            if in_range and cat_ok:
                matched.append(n)
        return {
            "success": True,
            "tool": self.name,
            "hypothesis_type": "competition",
            "row_count": len(matched),
            "data": matched,
        }


# ============================================================
# 工具注册
# ============================================================

def _clean_rows(rows: List[Dict]) -> List[Dict]:
    """
    清洗 DuckDB 返回行：将 date/Decimal/Timestamp 等转为 JSON 可序列化类型
    """
    cleaned = []
    for row in rows:
        clean = {}
        for k, v in row.items():
            if hasattr(v, "isoformat"):          # date/datetime/Timestamp
                clean[k] = v.isoformat()[:10] if not hasattr(v, "hour") else v.isoformat()
            elif hasattr(v, "__float__") and not isinstance(v, (int, float, bool)):
                clean[k] = float(v)              # Decimal
            else:
                clean[k] = v
        cleaned.append(clean)
    return cleaned


def register_diagnosis_tools(adapter: DatabaseAdapter) -> List[str]:
    """
    注册所有诊断工具到全局 tool_registry

    Args:
        adapter: DuckDB 适配器（供 DB 类工具使用）

    Returns:
        已注册的工具名称列表
    """
    tools: List[BaseTool] = [
        CampaignTool(adapter),
        InventoryTool(adapter),
        SellerTool(adapter),
        HolidayTool(),
        PolicyTool(),
        NewsTool(),
    ]
    for tool in tools:
        tool_registry.register(tool)

    names = [t.name for t in tools]
    logger.info("diagnosis_tools_registered", tools=names)
    return names
