"""
SignalPilot 合成数据生成器 V2

Phase 3 增强版：
- 扩展时间范围：2024-01-01 至 2026-07-12
- 两级分类体系（L1/L2）
- 基于业务关系的 KPI 生成
- 新增 inventory_daily 和 seller_daily_metrics
"""

import duckdb
import random
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# UTF-8 输出编码
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# 配置
SITES = ['US', 'DE', 'UK', 'AU', 'FR', 'IT', 'ES', 'CA', 'CN', 'JP']

# 两级分类体系（20个L1，每个5-10个L2）
CATEGORY_HIERARCHY = {
    1001: {'name': 'Electronics', 'asp_range': (50, 500), 'str_rate': (0.08, 0.15), 'children': {
        100101: {'name': 'Phones', 'asp_range': (200, 800)},
        100102: {'name': 'Laptops', 'asp_range': (400, 1500)},
        100103: {'name': 'Tablets', 'asp_range': (150, 600)},
        100104: {'name': 'Cameras', 'asp_range': (300, 1200)},
        100105: {'name': 'Audio', 'asp_range': (50, 400)},
        100106: {'name': 'Wearables', 'asp_range': (100, 500)},
        100107: {'name': 'Gaming Consoles', 'asp_range': (300, 600)},
    }},
    1002: {'name': 'Fashion', 'asp_range': (20, 200), 'str_rate': (0.15, 0.25), 'children': {
        100201: {'name': 'Men Clothing', 'asp_range': (30, 150)},
        100202: {'name': 'Women Clothing', 'asp_range': (25, 180)},
        100203: {'name': 'Kids Clothing', 'asp_range': (15, 80)},
        100204: {'name': 'Shoes', 'asp_range': (40, 200)},
        100205: {'name': 'Bags', 'asp_range': (50, 300)},
        100206: {'name': 'Accessories', 'asp_range': (10, 100)},
        100207: {'name': 'Watches', 'asp_range': (50, 500)},
    }},
    1003: {'name': 'Home & Garden', 'asp_range': (30, 300), 'str_rate': (0.10, 0.18), 'children': {
        100301: {'name': 'Furniture', 'asp_range': (100, 800)},
        100302: {'name': 'Kitchen', 'asp_range': (20, 200)},
        100303: {'name': 'Bedding', 'asp_range': (30, 150)},
        100304: {'name': 'Decor', 'asp_range': (15, 120)},
        100305: {'name': 'Garden Tools', 'asp_range': (25, 180)},
        100306: {'name': 'Lighting', 'asp_range': (20, 200)},
    }},
    1004: {'name': 'Sports & Outdoors', 'asp_range': (25, 250), 'str_rate': (0.12, 0.20), 'children': {
        100401: {'name': 'Fitness Equipment', 'asp_range': (50, 500)},
        100402: {'name': 'Cycling', 'asp_range': (100, 1000)},
        100403: {'name': 'Camping', 'asp_range': (30, 300)},
        100404: {'name': 'Sports Wear', 'asp_range': (20, 150)},
        100405: {'name': 'Water Sports', 'asp_range': (40, 400)},
    }},
    1005: {'name': 'Toys & Games', 'asp_range': (10, 100), 'str_rate': (0.20, 0.30), 'children': {
        100501: {'name': 'Action Figures', 'asp_range': (15, 80)},
        100502: {'name': 'Board Games', 'asp_range': (20, 100)},
        100503: {'name': 'Educational Toys', 'asp_range': (10, 60)},
        100504: {'name': 'Dolls', 'asp_range': (15, 100)},
        100505: {'name': 'Building Sets', 'asp_range': (25, 150)},
    }},
    1006: {'name': 'Books & Media', 'asp_range': (10, 50), 'str_rate': (0.18, 0.28), 'children': {
        100601: {'name': 'Books', 'asp_range': (10, 40)},
        100602: {'name': 'Music', 'asp_range': (5, 30)},
        100603: {'name': 'Movies', 'asp_range': (10, 50)},
        100604: {'name': 'Video Games', 'asp_range': (30, 70)},
    }},
    1007: {'name': 'Beauty & Health', 'asp_range': (15, 120), 'str_rate': (0.12, 0.22), 'children': {
        100701: {'name': 'Skincare', 'asp_range': (20, 150)},
        100702: {'name': 'Makeup', 'asp_range': (15, 100)},
        100703: {'name': 'Hair Care', 'asp_range': (10, 80)},
        100704: {'name': 'Vitamins', 'asp_range': (15, 60)},
        100705: {'name': 'Personal Care', 'asp_range': (10, 50)},
    }},
    1008: {'name': 'Automotive', 'asp_range': (20, 200), 'str_rate': (0.08, 0.15), 'children': {
        100801: {'name': 'Car Accessories', 'asp_range': (15, 150)},
        100802: {'name': 'Parts', 'asp_range': (30, 300)},
        100803: {'name': 'Tools', 'asp_range': (25, 200)},
        100804: {'name': 'Motorcycle', 'asp_range': (50, 500)},
    }},
    1009: {'name': 'Pet Supplies', 'asp_range': (10, 80), 'str_rate': (0.15, 0.25), 'children': {
        100901: {'name': 'Dog', 'asp_range': (10, 100)},
        100902: {'name': 'Cat', 'asp_range': (10, 80)},
        100903: {'name': 'Fish', 'asp_range': (5, 50)},
        100904: {'name': 'Bird', 'asp_range': (10, 60)},
    }},
    1010: {'name': 'Baby & Kids', 'asp_range': (15, 150), 'str_rate': (0.14, 0.24), 'children': {
        101001: {'name': 'Baby Gear', 'asp_range': (50, 300)},
        101002: {'name': 'Baby Food', 'asp_range': (10, 50)},
        101003: {'name': 'Diapers', 'asp_range': (20, 60)},
        101004: {'name': 'Baby Toys', 'asp_range': (10, 80)},
    }},
    1011: {'name': 'Jewelry', 'asp_range': (30, 500), 'str_rate': (0.06, 0.12), 'children': {
        101101: {'name': 'Necklaces', 'asp_range': (40, 600)},
        101102: {'name': 'Rings', 'asp_range': (50, 1000)},
        101103: {'name': 'Earrings', 'asp_range': (20, 300)},
        101104: {'name': 'Bracelets', 'asp_range': (30, 400)},
    }},
    1012: {'name': 'Office', 'asp_range': (10, 150), 'str_rate': (0.10, 0.18), 'children': {
        101201: {'name': 'Furniture', 'asp_range': (100, 800)},
        101202: {'name': 'Supplies', 'asp_range': (5, 50)},
        101203: {'name': 'Electronics', 'asp_range': (50, 300)},
    }},
    1013: {'name': 'Tools & Hardware', 'asp_range': (20, 200), 'str_rate': (0.09, 0.16), 'children': {
        101301: {'name': 'Power Tools', 'asp_range': (80, 400)},
        101302: {'name': 'Hand Tools', 'asp_range': (15, 100)},
        101303: {'name': 'Hardware', 'asp_range': (5, 50)},
    }},
    1014: {'name': 'Grocery', 'asp_range': (5, 50), 'str_rate': (0.25, 0.35), 'children': {
        101401: {'name': 'Snacks', 'asp_range': (3, 20)},
        101402: {'name': 'Beverages', 'asp_range': (5, 30)},
        101403: {'name': 'Pantry', 'asp_range': (10, 50)},
    }},
    1015: {'name': 'Handmade & Crafts', 'asp_range': (15, 120), 'str_rate': (0.10, 0.18), 'children': {
        101501: {'name': 'Handmade Items', 'asp_range': (20, 150)},
        101502: {'name': 'Craft Supplies', 'asp_range': (10, 80)},
        101503: {'name': 'Art', 'asp_range': (30, 300)},
    }},
    1016: {'name': 'Industrial', 'asp_range': (50, 500), 'str_rate': (0.05, 0.10), 'children': {
        101601: {'name': 'Equipment', 'asp_range': (200, 2000)},
        101602: {'name': 'Supplies', 'asp_range': (30, 300)},
    }},
    1017: {'name': 'Luggage & Travel', 'asp_range': (40, 300), 'str_rate': (0.11, 0.19), 'children': {
        101701: {'name': 'Suitcases', 'asp_range': (60, 400)},
        101702: {'name': 'Backpacks', 'asp_range': (30, 150)},
        101703: {'name': 'Travel Accessories', 'asp_range': (10, 80)},
    }},
    1018: {'name': 'Appliances', 'asp_range': (100, 800), 'str_rate': (0.07, 0.14), 'children': {
        101801: {'name': 'Kitchen Appliances', 'asp_range': (50, 500)},
        101802: {'name': 'Home Appliances', 'asp_range': (100, 1000)},
        101803: {'name': 'Small Appliances', 'asp_range': (30, 200)},
    }},
    1019: {'name': 'Software & Digital', 'asp_range': (20, 150), 'str_rate': (0.20, 0.30), 'children': {
        101901: {'name': 'Software', 'asp_range': (30, 200)},
        101902: {'name': 'Digital Downloads', 'asp_range': (10, 100)},
    }},
    1020: {'name': 'Collectibles', 'asp_range': (30, 300), 'str_rate': (0.08, 0.15), 'children': {
        102001: {'name': 'Coins', 'asp_range': (50, 500)},
        102002: {'name': 'Stamps', 'asp_range': (20, 200)},
        102003: {'name': 'Trading Cards', 'asp_range': (10, 100)},
        102004: {'name': 'Memorabilia', 'asp_range': (40, 400)},
    }},
}

# 生成所有 L2 分类列表
ALL_L2_CATEGORIES = []
for l1_id, l1_data in CATEGORY_HIERARCHY.items():
    for l2_id, l2_data in l1_data['children'].items():
        ALL_L2_CATEGORIES.append({
            'l1_id': l1_id,
            'l1_name': l1_data['name'],
            'l2_id': l2_id,
            'l2_name': l2_data['name'],
            'asp_range': l2_data['asp_range'],
            'str_rate': l1_data['str_rate']
        })

print(f"[INFO] 生成的分类数量: {len(ALL_L2_CATEGORIES)} 个 L2 分类")

START_DATE = datetime(2024, 1, 1)
END_DATE = datetime(2026, 7, 12)
ANOMALY_RATE = 0.05

def create_database():
    """创建数据库和表结构"""
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)
    db_path = data_dir / 'signal.db'
    
    if db_path.exists():
        print(f"[WARNING] 删除旧数据库: {db_path}")
        db_path.unlink()
    
    conn = duckdb.connect(str(db_path))
    print("[INFO] 创建表结构...")
    
    # daily_metrics 表（升级版）
    conn.execute("""
        CREATE TABLE daily_metrics (
            date DATE NOT NULL,
            site VARCHAR NOT NULL,
            category_l1 VARCHAR NOT NULL,
            category_l2 VARCHAR NOT NULL,
            category_id_l1 INTEGER NOT NULL,
            category_id_l2 INTEGER NOT NULL,
            gmv DECIMAL(15, 2),
            sold_items INTEGER,
            live_listings INTEGER,
            str DECIMAL(5, 4),
            impressions INTEGER,
            clicks INTEGER,
            orders INTEGER,
            ctr DECIMAL(5, 4),
            cvr DECIMAL(5, 4),
            asp DECIMAL(10, 2),
            active_sellers INTEGER,
            new_listings INTEGER,
            PRIMARY KEY (date, site, category_id_l1, category_id_l2)
        )
    """)
    
    # inventory_daily 表
    conn.execute("""
        CREATE TABLE inventory_daily (
            date DATE NOT NULL,
            site VARCHAR NOT NULL,
            category_id_l1 INTEGER NOT NULL,
            category_l1 VARCHAR NOT NULL,
            category_id_l2 INTEGER NOT NULL,
            category_l2 VARCHAR NOT NULL,
            live_listings INTEGER,
            available_inventory INTEGER,
            out_of_stock_rate DECIMAL(5, 4),
            days_of_supply DECIMAL(8, 2),
            restock_qty INTEGER,
            inventory_health VARCHAR,
            PRIMARY KEY (date, site, category_id_l1, category_id_l2)
        )
    """)
    
    # seller_daily_metrics 表
    conn.execute("""
        CREATE TABLE seller_daily_metrics (
            date DATE NOT NULL,
            site VARCHAR NOT NULL,
            category_id_l1 INTEGER NOT NULL,
            category_l1 VARCHAR NOT NULL,
            category_id_l2 INTEGER NOT NULL,
            category_l2 VARCHAR NOT NULL,
            seller_id VARCHAR NOT NULL,
            seller_name VARCHAR,
            gmv DECIMAL(15, 2),
            sold_items INTEGER,
            orders INTEGER,
            asp DECIMAL(10, 2),
            impressions INTEGER,
            clicks INTEGER,
            ctr DECIMAL(5, 4),
            cvr DECIMAL(5, 4),
            seller_share DECIMAL(5, 4),
            seller_rank INTEGER,
            PRIMARY KEY (date, site, category_id_l1, category_id_l2, seller_id)
        )
    """)
    
    # campaigns 表（保持兼容，添加 L1/L2 字段）
    conn.execute("""
        CREATE TABLE campaigns (
            campaign_id VARCHAR PRIMARY KEY,
            campaign_name VARCHAR NOT NULL,
            site VARCHAR NOT NULL,
            category_id_l1 INTEGER,
            category_l1 VARCHAR,
            category_id_l2 INTEGER,
            category_l2 VARCHAR,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            discount_rate DECIMAL(5, 2),
            subsidy_budget DECIMAL(12, 2),
            target_gmv DECIMAL(15, 2),
            actual_gmv DECIMAL(15, 2),
            roi DECIMAL(5, 2)
        )
    """)
    
    # sellers 表（保持不变）
    conn.execute("""
        CREATE TABLE sellers (
            seller_id VARCHAR PRIMARY KEY,
            seller_name VARCHAR NOT NULL,
            site VARCHAR NOT NULL,
            country VARCHAR NOT NULL,
            join_date DATE NOT NULL,
            feedback_score INTEGER DEFAULT 0,
            is_top_rated BOOLEAN DEFAULT FALSE,
            status VARCHAR DEFAULT 'active',
            last_listing_date DATE
        )
    """)
    
    print("[OK] 表结构创建完成")
    return conn

print("[START] 准备生成数据...")


def generate_daily_metrics(conn):
    """生成 daily_metrics 数据（支持断点续传）"""
    print(f"\n[INFO] 生成 daily_metrics 数据...")
    print(f"   时间范围: {START_DATE.date()} 到 {END_DATE.date()}")
    print(f"   站点数: {len(SITES)}")
    print(f"   L2 分类数: {len(ALL_L2_CATEGORIES)}")

    # 检查已有数据，从最后一天继续
    existing_max_date = conn.execute("SELECT MAX(date) FROM daily_metrics").fetchone()[0]
    if existing_max_date:
        from datetime import datetime as dt
        existing_max_date = dt.strptime(str(existing_max_date), '%Y-%m-%d')
        if existing_max_date >= END_DATE:
            print(f"   [INFO] 数据已完整，跳过生成")
            # 读取现有数据
            data_from_db = conn.execute("""
                SELECT date, site, category_id_l1, category_l1, category_id_l2, category_l2,
                       gmv, sold_items, live_listings, str, impressions, clicks, orders,
                       ctr, cvr, asp, active_sellers, new_listings
                FROM daily_metrics
                ORDER BY date, site, category_id_l2
            """).fetchall()
            data_list = [{
                'date': row[0], 'site': row[1], 'category_id_l1': row[2], 'category_l1': row[3],
                'category_id_l2': row[4], 'category_l2': row[5], 'gmv': row[6], 'sold_items': row[7],
                'live_listings': row[8], 'str': row[9], 'impressions': row[10], 'clicks': row[11],
                'orders': row[12], 'ctr': row[13], 'cvr': row[14], 'asp': row[15],
                'active_sellers': row[16], 'new_listings': row[17]
            } for row in data_from_db]
            print(f"[OK] daily_metrics 已存在: {len(data_list):,} 行")
            return data_list
        else:
            current_date = existing_max_date + timedelta(days=1)
            existing_count = conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0]
            print(f"   [INFO] 从 {current_date.date()} 继续生成（已有 {existing_count:,} 行）")
    else:
        current_date = START_DATE

    data = []
    total_days = (END_DATE - START_DATE).days + 1
    day_count = (current_date - START_DATE).days
    BATCH_SIZE = 50000  # 每50k行插入一次

    # 为每个 (site, category_l2) 设置基线指标
    baselines = {}
    for site in SITES:
        for cat in ALL_L2_CATEGORIES:
            key = (site, cat['l2_id'])
            baselines[key] = {
                'live_listings': int(random.uniform(5000, 50000)),
                'str': random.uniform(cat['str_rate'][0], cat['str_rate'][1]),
                'asp': random.uniform(cat['asp_range'][0], cat['asp_range'][1]),
                'ctr': random.uniform(0.015, 0.045),
                'cvr': random.uniform(0.025, 0.075),
            }

    while current_date <= END_DATE:
        day_count += 1

        # 周末效应
        is_weekend = current_date.weekday() in [5, 6]
        weekend_multiplier = 1.2 if is_weekend else 1.0

        # 季节性效应
        if current_date.month in [11, 12]:
            seasonal_multiplier = 1.5
        elif current_date.month in [1, 2]:
            seasonal_multiplier = 1.3
        else:
            seasonal_multiplier = 1.0

        for site in SITES:
            # 每天随机选择 70-90% 的分类有数据
            active_categories = random.sample(ALL_L2_CATEGORIES,
                                            k=int(len(ALL_L2_CATEGORIES) * random.uniform(0.7, 0.9)))

            for cat in active_categories:
                key = (site, cat['l2_id'])
                baseline = baselines[key]

                # 基础指标（加入随机波动）
                live_listings = int(baseline['live_listings'] * random.uniform(0.90, 1.10))
                str_rate = baseline['str'] * random.uniform(0.85, 1.15)
                asp = baseline['asp'] * random.uniform(0.90, 1.10)
                base_ctr = baseline['ctr'] * random.uniform(0.9, 1.1)
                base_cvr = baseline['cvr'] * random.uniform(0.9, 1.1)

                # 应用季节性和周末效应
                str_rate *= weekend_multiplier * seasonal_multiplier * random.uniform(0.95, 1.05)

                # 注入异常
                if random.random() < ANOMALY_RATE:
                    anomaly_type = random.choice(['traffic_drop', 'conversion_drop', 'spike'])
                    if anomaly_type == 'traffic_drop':
                        live_listings = int(live_listings * random.uniform(0.5, 0.7))
                    elif anomaly_type == 'conversion_drop':
                        str_rate *= random.uniform(0.6, 0.7)
                    elif anomaly_type == 'spike':
                        str_rate *= random.uniform(1.5, 2.0)

                # 计算衍生指标
                # STR = Sold Items / Live Listings
                sold_items = int(live_listings * str_rate)

                # GMV = ASP × Sold Items（精确计算后再舍入）
                gmv = round(asp * sold_items, 2)

                # Impressions ≈ Live Listings (流量与库存相关)
                impressions = int(live_listings * random.uniform(0.8, 1.2) * weekend_multiplier * seasonal_multiplier)

                # Clicks = Impressions × CTR
                clicks = int(impressions * base_ctr)

                # Orders = Clicks × CVR
                orders = int(clicks * base_cvr)

                # Active Sellers
                active_sellers = int(random.uniform(10, 100))
                new_listings = int(random.uniform(50, 500))

                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'site': site,
                    'category_l1': cat['l1_name'],
                    'category_l2': cat['l2_name'],
                    'category_id_l1': cat['l1_id'],
                    'category_id_l2': cat['l2_id'],
                    'gmv': round(gmv, 2),
                    'sold_items': sold_items,
                    'live_listings': live_listings,
                    'str': round(str_rate, 4),
                    'impressions': impressions,
                    'clicks': clicks,
                    'orders': orders,
                    'ctr': round(base_ctr, 4),
                    'cvr': round(base_cvr, 4),
                    'asp': round(asp, 2),
                    'active_sellers': active_sellers,
                    'new_listings': new_listings
                })

                # 分批插入
                if len(data) >= BATCH_SIZE:
                    print(f"   [INFO] 插入批次数据 ({len(data):,} 行)...")
                    conn.executemany("""
                        INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [(
                        d['date'], d['site'], d['category_l1'], d['category_l2'],
                        d['category_id_l1'], d['category_id_l2'], d['gmv'], d['sold_items'],
                        d['live_listings'], d['str'], d['impressions'], d['clicks'], d['orders'],
                        d['ctr'], d['cvr'], d['asp'], d['active_sellers'], d['new_listings']
                    ) for d in data])
                    conn.commit()  # 提交事务
                    data = []  # 清空缓存

        current_date += timedelta(days=1)

        # 进度显示
        if day_count % 50 == 0:
            progress = (day_count / total_days) * 100
            current_total = conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0]
            print(f"   进度: {progress:.1f}% (已插入 {current_total:,} 行)")

    # 插入剩余数据
    if data:
        print(f"   [INFO] 插入最后批次数据 ({len(data):,} 行)...")
        conn.executemany("""
            INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(
            d['date'], d['site'], d['category_l1'], d['category_l2'],
            d['category_id_l1'], d['category_id_l2'], d['gmv'], d['sold_items'],
            d['live_listings'], d['str'], d['impressions'], d['clicks'], d['orders'],
            d['ctr'], d['cvr'], d['asp'], d['active_sellers'], d['new_listings']
        ) for d in data])
        conn.commit()
    conn.executemany("""
        INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        d['date'], d['site'], d['category_l1'], d['category_l2'],
        d['category_id_l1'], d['category_id_l2'], d['gmv'], d['sold_items'],
        d['live_listings'], d['str'], d['impressions'], d['clicks'],
        d['orders'], d['ctr'], d['cvr'], d['asp'], d['active_sellers'], d['new_listings']
    ) for d in data])

    # 创建索引
    print("   [INFO] 创建索引...")
    conn.execute("CREATE INDEX idx_daily_date ON daily_metrics(date)")
    conn.execute("CREATE INDEX idx_daily_site_cat ON daily_metrics(site, category_id_l1, category_id_l2)")

    # 从数据库重新读取数据（用于后续处理）
    print("   [INFO] 读取生成的数据...")
    total_count = conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()[0]
    data_from_db = conn.execute("""
        SELECT date, site, category_id_l1, category_l1, category_id_l2, category_l2,
               gmv, sold_items, live_listings, str, impressions, clicks, orders,
               ctr, cvr, asp, active_sellers, new_listings
        FROM daily_metrics
        ORDER BY date, site, category_id_l2
    """).fetchall()

    # 转换为字典列表
    data_list = [{
        'date': row[0], 'site': row[1], 'category_id_l1': row[2], 'category_l1': row[3],
        'category_id_l2': row[4], 'category_l2': row[5], 'gmv': row[6], 'sold_items': row[7],
        'live_listings': row[8], 'str': row[9], 'impressions': row[10], 'clicks': row[11],
        'orders': row[12], 'ctr': row[13], 'cvr': row[14], 'asp': row[15],
        'active_sellers': row[16], 'new_listings': row[17]
    } for row in data_from_db]

    print(f"[OK] daily_metrics 生成完成: {total_count:,} 行")
    return data_list


def generate_inventory_daily(conn, daily_metrics_data):
    """生成 inventory_daily 数据（基于 daily_metrics）"""
    print(f"\n[INFO] 生成 inventory_daily 数据...")

    inventory_data = []
    BATCH_SIZE = 50000  # 每50k行插入一次
    processed = 0

    for dm in daily_metrics_data:
        # 基于 daily_metrics 的 live_listings
        live_listings = dm['live_listings']
        sold_items = dm['sold_items']

        # Available Inventory = Live Listings × (1-10 件/listing)
        available_inventory = int(live_listings * random.uniform(1, 10))

        # Out of Stock Rate (5-20%)
        out_of_stock_rate = random.uniform(0.05, 0.20)

        # Days of Supply = Available Inventory / Daily Sold Items
        days_of_supply = available_inventory / sold_items if sold_items > 0 else 999

        # Restock Qty (补货量)
        restock_qty = int(sold_items * random.uniform(0.8, 1.2))

        # Inventory Health
        if days_of_supply < 7:
            inventory_health = 'Low'
        elif days_of_supply < 30:
            inventory_health = 'Healthy'
        else:
            inventory_health = 'Excess'

        inventory_data.append({
            'date': dm['date'],
            'site': dm['site'],
            'category_id_l1': dm['category_id_l1'],
            'category_l1': dm['category_l1'],
            'category_id_l2': dm['category_id_l2'],
            'category_l2': dm['category_l2'],
            'live_listings': live_listings,
            'available_inventory': available_inventory,
            'out_of_stock_rate': round(out_of_stock_rate, 4),
            'days_of_supply': round(days_of_supply, 2),
            'restock_qty': restock_qty,
            'inventory_health': inventory_health
        })

        # 分批插入
        if len(inventory_data) >= BATCH_SIZE:
            print(f"   [INFO] 插入批次数据 ({len(inventory_data):,} 行)...")
            conn.executemany("""
                INSERT INTO inventory_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [(
                inv['date'], inv['site'], inv['category_id_l1'], inv['category_l1'],
                inv['category_id_l2'], inv['category_l2'], inv['live_listings'],
                inv['available_inventory'], inv['out_of_stock_rate'],
                inv['days_of_supply'], inv['restock_qty'], inv['inventory_health']
            ) for inv in inventory_data])
            conn.commit()
            inventory_data = []

        processed += 1
        if processed % 50000 == 0:
            progress = (processed / len(daily_metrics_data)) * 100
            current_total = conn.execute("SELECT COUNT(*) FROM inventory_daily").fetchone()[0]
            print(f"   进度: {progress:.1f}% (已插入 {current_total:,} 行)")

    # 插入剩余数据
    if inventory_data:
        print(f"   [INFO] 插入最后批次数据 ({len(inventory_data):,} 行)...")
        conn.executemany("""
            INSERT INTO inventory_daily VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(
            inv['date'], inv['site'], inv['category_id_l1'], inv['category_l1'],
            inv['category_id_l2'], inv['category_l2'], inv['live_listings'],
            inv['available_inventory'], inv['out_of_stock_rate'],
            inv['days_of_supply'], inv['restock_qty'], inv['inventory_health']
        ) for inv in inventory_data])
        conn.commit()

    # 获取最终总数
    total_count = conn.execute("SELECT COUNT(*) FROM inventory_daily").fetchone()[0]
    print(f"[OK] inventory_daily 生成完成: {total_count:,} 行")
    return total_count


def generate_seller_daily_metrics(conn, daily_metrics_data):
    """生成 seller_daily_metrics 数据（Top-down 分配）"""
    print(f"\n[INFO] 生成 seller_daily_metrics 数据...")

    # 为每个 (site, category_l2) 生成 5-10 个卖家
    seller_pool = {}
    for site in SITES:
        for cat in ALL_L2_CATEGORIES:
            key = (site, cat['l2_id'])
            num_sellers = random.randint(5, 10)
            sellers = []
            for i in range(num_sellers):
                seller_id = f"SELLER_{site}_{cat['l2_id']}_{i+1:03d}"
                sellers.append({
                    'seller_id': seller_id,
                    'seller_name': f"Shop_{random.randint(1000, 9999)}",
                    'share': random.uniform(0.05, 0.25)  # 每个卖家的市场份额
                })
            # 归一化份额
            total_share = sum(s['share'] for s in sellers)
            for s in sellers:
                s['share'] /= total_share
            seller_pool[key] = sellers

    seller_data = []
    processed = 0
    BATCH_SIZE = 50000  # 每50k行插入一次，避免内存溢出

    for dm in daily_metrics_data:
        key = (dm['site'], dm['category_id_l2'])
        sellers = seller_pool.get(key, [])

        # Top-down 分配：将 daily_metrics 的 GMV 分配给各个卖家
        for rank, seller in enumerate(sellers, start=1):
            seller_gmv = dm['gmv'] * seller['share']
            seller_sold_items = int(dm['sold_items'] * seller['share'])
            seller_orders = int(dm['orders'] * seller['share'])
            seller_impressions = int(dm['impressions'] * seller['share'])
            seller_clicks = int(dm['clicks'] * seller['share'])

            # ASP = GMV / Sold Items
            seller_asp = seller_gmv / seller_sold_items if seller_sold_items > 0 else 0

            seller_data.append({
                'date': dm['date'],
                'site': dm['site'],
                'category_id_l1': dm['category_id_l1'],
                'category_l1': dm['category_l1'],
                'category_id_l2': dm['category_id_l2'],
                'category_l2': dm['category_l2'],
                'seller_id': seller['seller_id'],
                'seller_name': seller['seller_name'],
                'gmv': round(seller_gmv, 2),
                'sold_items': seller_sold_items,
                'orders': seller_orders,
                'asp': round(seller_asp, 2),
                'impressions': seller_impressions,
                'clicks': seller_clicks,
                'ctr': dm['ctr'],  # 继承分类的 CTR
                'cvr': dm['cvr'],  # 继承分类的 CVR
                'seller_share': round(seller['share'], 4),
                'seller_rank': rank
            })

            # 分批插入，避免内存溢出
            if len(seller_data) >= BATCH_SIZE:
                print(f"   [INFO] 插入批次数据 ({len(seller_data):,} 行)...")
                conn.executemany("""
                    INSERT INTO seller_daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, [(
                    s['date'], s['site'], s['category_id_l1'], s['category_l1'],
                    s['category_id_l2'], s['category_l2'], s['seller_id'], s['seller_name'],
                    s['gmv'], s['sold_items'], s['orders'], s['asp'], s['impressions'],
                    s['clicks'], s['ctr'], s['cvr'], s['seller_share'], s['seller_rank']
                ) for s in seller_data])
                conn.commit()  # 提交事务
                seller_data = []  # 清空缓存

        processed += 1
        if processed % 10000 == 0:
            progress = (processed / len(daily_metrics_data)) * 100
            current_total = conn.execute("SELECT COUNT(*) FROM seller_daily_metrics").fetchone()[0]
            print(f"   进度: {progress:.1f}% (已插入 {current_total:,} 行)")

    # 插入剩余数据
    if seller_data:
        print(f"   [INFO] 插入最后批次数据 ({len(seller_data):,} 行)...")
        conn.executemany("""
            INSERT INTO seller_daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [(
            s['date'], s['site'], s['category_id_l1'], s['category_l1'],
            s['category_id_l2'], s['category_l2'], s['seller_id'], s['seller_name'],
            s['gmv'], s['sold_items'], s['orders'], s['asp'], s['impressions'],
            s['clicks'], s['ctr'], s['cvr'], s['seller_share'], s['seller_rank']
        ) for s in seller_data])
        conn.commit()

    # 获取最终总数
    total_count = conn.execute("SELECT COUNT(*) FROM seller_daily_metrics").fetchone()[0]
    print(f"[OK] seller_daily_metrics 生成完成: {total_count:,} 行")
    return total_count


def generate_campaigns(conn):
    """生成 campaigns 数据"""
    print(f"\n[INFO] 生成 campaigns 数据...")

    campaigns = []
    campaign_names = [
        'Black Friday 2024',
        'Cyber Monday 2024',
        'Christmas Sale 2024',
        'New Year Deals 2025',
        'Spring Festival 2025',
        'Valentine Special 2025',
        'Easter Sale 2025',
        'Summer Blast 2025',
        'Back to School 2025',
        'Halloween Special 2025',
        'Black Friday 2025',
        'Cyber Monday 2025',
        'Christmas Sale 2025',
        'New Year Deals 2026',
        'Spring Festival 2026',
        'Easter Sale 2026',
    ]

    campaign_dates = [
        ('2024-11-25', '2024-11-28'),
        ('2024-11-29', '2024-12-01'),
        ('2024-12-15', '2024-12-25'),
        ('2025-01-01', '2025-01-07'),
        ('2025-02-10', '2025-02-17'),
        ('2025-02-12', '2025-02-16'),
        ('2025-04-10', '2025-04-20'),
        ('2025-06-15', '2025-06-30'),
        ('2025-08-15', '2025-09-05'),
        ('2025-10-25', '2025-10-31'),
        ('2025-11-25', '2025-11-28'),
        ('2025-11-29', '2025-12-01'),
        ('2025-12-15', '2025-12-25'),
        ('2026-01-01', '2026-01-07'),
        ('2026-02-10', '2026-02-17'),
        ('2026-04-10', '2026-04-20'),
    ]

    for i, (name, (start, end)) in enumerate(zip(campaign_names, campaign_dates)):
        for site in random.sample(SITES, k=random.randint(3, 6)):
            campaign_id = f"CAMP_{i+1:03d}_{site}"

            # 随机选择一个 L2 分类或全站
            if random.random() < 0.3:  # 30% 全站活动
                category_l1 = None
                category_l2 = None
                category_id_l1 = None
                category_id_l2 = None
            else:
                cat = random.choice(ALL_L2_CATEGORIES)
                category_l1 = cat['l1_name']
                category_l2 = cat['l2_name']
                category_id_l1 = cat['l1_id']
                category_id_l2 = cat['l2_id']

            discount = random.uniform(0.10, 0.30)
            subsidy = random.uniform(10000, 100000)
            target_gmv = subsidy / discount * random.uniform(8, 15)
            actual_gmv = target_gmv * random.uniform(0.7, 1.3)
            roi = (actual_gmv - subsidy) / subsidy if subsidy > 0 else 0

            campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': name,
                'site': site,
                'category_id_l1': category_id_l1,
                'category_l1': category_l1,
                'category_id_l2': category_id_l2,
                'category_l2': category_l2,
                'start_date': start,
                'end_date': end,
                'discount_rate': round(discount, 2),
                'subsidy_budget': round(subsidy, 2),
                'target_gmv': round(target_gmv, 2),
                'actual_gmv': round(actual_gmv, 2),
                'roi': round(roi, 2)
            })

    conn.executemany("""
        INSERT INTO campaigns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        c['campaign_id'], c['campaign_name'], c['site'],
        c['category_id_l1'], c['category_l1'], c['category_id_l2'], c['category_l2'],
        c['start_date'], c['end_date'], c['discount_rate'],
        c['subsidy_budget'], c['target_gmv'], c['actual_gmv'], c['roi']
    ) for c in campaigns])

    print(f"[OK] campaigns 生成完成: {len(campaigns)} 个活动")
    return len(campaigns)


def generate_sellers(conn):
    """生成 sellers 数据"""
    print(f"\n[INFO] 生成 sellers 数据...")

    sellers = []
    seller_count = 1000

    countries = ['US', 'CN', 'UK', 'DE', 'AU', 'JP', 'FR', 'CA', 'IT', 'ES']

    for i in range(seller_count):
        seller_id = f"SELLER_{i+1:05d}"
        site = random.choice(SITES)
        country = random.choice(countries)

        days_ago = random.randint(30, 900)
        join_date = END_DATE - timedelta(days=days_ago)

        days_since_listing = random.randint(0, 30)
        last_listing = END_DATE - timedelta(days=days_since_listing)

        status = random.choices(
            ['active', 'suspended', 'churned'],
            weights=[0.90, 0.05, 0.05]
        )[0]

        sellers.append({
            'seller_id': seller_id,
            'seller_name': f"Shop_{i+1}",
            'site': site,
            'country': country,
            'join_date': join_date.strftime('%Y-%m-%d'),
            'feedback_score': random.randint(0, 10000),
            'is_top_rated': random.random() < 0.2,
            'status': status,
            'last_listing_date': last_listing.strftime('%Y-%m-%d')
        })

    conn.executemany("""
        INSERT INTO sellers VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        s['seller_id'], s['seller_name'], s['site'], s['country'],
        s['join_date'], s['feedback_score'], s['is_top_rated'],
        s['status'], s['last_listing_date']
    ) for s in sellers])

    print(f"[OK] sellers 生成完成: {len(sellers)} 个卖家")
    return len(sellers)


def print_summary(conn):
    """打印数据摘要"""
    print("\n" + "="*60)
    print("[SUMMARY] 数据生成摘要")
    print("="*60)

    # daily_metrics 统计
    result = conn.execute("SELECT COUNT(*) FROM daily_metrics").fetchone()
    print(f"daily_metrics:        {result[0]:,} 行")

    result = conn.execute("SELECT MIN(date), MAX(date) FROM daily_metrics").fetchone()
    print(f"  日期范围:           {result[0]} 到 {result[1]}")

    result = conn.execute("SELECT COUNT(DISTINCT site) FROM daily_metrics").fetchone()
    print(f"  站点数:             {result[0]}")

    result = conn.execute("SELECT COUNT(DISTINCT category_id_l1) FROM daily_metrics").fetchone()
    print(f"  L1 分类数:          {result[0]}")

    result = conn.execute("SELECT COUNT(DISTINCT category_id_l2) FROM daily_metrics").fetchone()
    print(f"  L2 分类数:          {result[0]}")

    result = conn.execute("SELECT SUM(gmv) FROM daily_metrics").fetchone()
    print(f"  总 GMV:             ${result[0]:,.2f}")

    # inventory_daily 统计
    result = conn.execute("SELECT COUNT(*) FROM inventory_daily").fetchone()
    print(f"\ninventory_daily:      {result[0]:,} 行")

    # seller_daily_metrics 统计
    result = conn.execute("SELECT COUNT(*) FROM seller_daily_metrics").fetchone()
    print(f"seller_daily_metrics: {result[0]:,} 行")

    result = conn.execute("SELECT COUNT(DISTINCT seller_id) FROM seller_daily_metrics").fetchone()
    print(f"  唯一卖家数:         {result[0]:,}")

    # campaigns 统计
    result = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()
    print(f"\ncampaigns:            {result[0]} 个活动")

    # sellers 统计
    result = conn.execute("SELECT COUNT(*) FROM sellers").fetchone()
    print(f"sellers:              {result[0]} 个卖家")

    # 示例查询
    print("\n" + "-"*60)
    print("[EXAMPLE] 示例查询：US 站 Phones 最近 7 天数据")
    print("-"*60)

    result = conn.execute("""
        SELECT date, category_l2, gmv, sold_items, str
        FROM daily_metrics
        WHERE site = 'US' AND category_id_l2 = 100101
        ORDER BY date DESC
        LIMIT 7
    """).fetchall()

    for row in result:
        print(f"  {row[0]} {row[1]}: ${row[2]:,.2f}, {row[3]:,} items, STR {row[4]:.2%}")

    print("="*60)


def main():
    """主函数"""
    print("="*60)
    print("SignalPilot 数据生成器 V2")
    print("="*60)

    try:
        # 创建数据库
        conn = create_database()

        # 生成数据
        print("\n[STEP 1/5] 生成 daily_metrics...")
        daily_data = generate_daily_metrics(conn)
        print(f"✓ 完成: {len(daily_data):,} 行")

        print("\n[STEP 2/5] 生成 inventory_daily...")
        generate_inventory_daily(conn, daily_data)
        print("✓ 完成")

        print("\n[STEP 3/5] 生成 seller_daily_metrics...")
        generate_seller_daily_metrics(conn, daily_data)
        print("✓ 完成")

        print("\n[STEP 4/5] 生成 campaigns...")
        generate_campaigns(conn)
        print("✓ 完成")

        print("\n[STEP 5/5] 生成 sellers...")
        generate_sellers(conn)
        print("✓ 完成")

        # 打印摘要
        print_summary(conn)

        # 关闭连接
        conn.close()

        print("\n[SUCCESS] 数据生成完成!")
        print(f"[FILE] 数据库文件: {Path(__file__).parent / 'signal.db'}")
        print("\n[NEXT] 下一步:")
        print("   cd backend")
        print("   uvicorn app.main:app --reload")

    except Exception as e:
        print(f"\n[ERROR] 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
