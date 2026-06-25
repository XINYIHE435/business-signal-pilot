"""
SignalPilot 合成数据生成器

生成模拟 eBay 跨境业务的合成数据，包含：
- daily_metrics: 每日业务指标（GMV, SI, CTR, CVR, ASP 等）
- campaigns: 促销活动
- sellers: 卖家信息
- anomalies: 异常记录

注入 5 种异常模式：
1. Traffic Drop（流量骤降）
2. Conversion Issue（转化率下降）
3. Campaign Overlap（促销冲突）
4. Seller Churn（卖家流失）
5. Seasonality Spike（季节性波动）
"""

import duckdb
import random
from datetime import datetime, timedelta
import sys
import os
from pathlib import Path

# 设置 UTF-8 输出编码（Windows 兼容）
if sys.platform == 'win32':
    os.system('chcp 65001 > nul 2>&1')
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None

# 配置
SITES = ['US', 'DE', 'UK', 'AU', 'FR', 'IT', 'ES', 'CA', 'CN', 'JP']
CATEGORIES = [
    'Electronics', 'Fashion', 'Home', 'Sports', 'Toys',
    'Books', 'Beauty', 'Automotive', 'Health', 'Garden',
    'Pet', 'Baby', 'Jewelry', 'Office', 'Music',
    'Video Games', 'Tools', 'Grocery', 'Handmade', 'Industrial',
    'Luggage', 'Shoes', 'Watches', 'Appliances', 'Furniture',
    'Arts', 'Crafts', 'Outdoor', 'Software', 'Collectibles'
]

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2026, 12, 31)

# 异常注入概率
ANOMALY_RATE = 0.05  # 5% 的数据点包含异常


def create_database():
    """创建数据库和表结构"""

    # 确保 data 目录存在
    data_dir = Path(__file__).parent
    data_dir.mkdir(exist_ok=True)

    db_path = data_dir / 'signal.db'

    # 如果数据库已存在，删除
    if db_path.exists():
        print(f"[WARNING] 数据库已存在，删除旧文件: {db_path}")
        db_path.unlink()

    conn = duckdb.connect(str(db_path))

    print("[INFO] 创建表结构...")

    # daily_metrics 表
    conn.execute("""
        CREATE TABLE daily_metrics (
            date DATE NOT NULL,
            site VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            gmv DECIMAL(15, 2),
            sold_items INTEGER,
            impressions INTEGER,
            clicks INTEGER,
            orders INTEGER,
            ctr DECIMAL(5, 4),
            cvr DECIMAL(5, 4),
            asp DECIMAL(10, 2),
            active_sellers INTEGER,
            new_listings INTEGER,
            PRIMARY KEY (date, site, category)
        )
    """)

    # campaigns 表
    conn.execute("""
        CREATE TABLE campaigns (
            campaign_id VARCHAR PRIMARY KEY,
            campaign_name VARCHAR NOT NULL,
            site VARCHAR NOT NULL,
            category VARCHAR,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            discount_rate DECIMAL(5, 2),
            subsidy_budget DECIMAL(12, 2),
            target_gmv DECIMAL(15, 2),
            actual_gmv DECIMAL(15, 2),
            roi DECIMAL(5, 2)
        )
    """)

    # sellers 表
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

    # anomalies 表（用于记录检测到的异常）
    conn.execute("""
        CREATE TABLE anomalies (
            id VARCHAR PRIMARY KEY,
            detected_at TIMESTAMP NOT NULL,
            date DATE NOT NULL,
            metric_name VARCHAR NOT NULL,
            site VARCHAR,
            category VARCHAR,
            expected_value DECIMAL(15, 2),
            actual_value DECIMAL(15, 2),
            deviation_percent DECIMAL(5, 2),
            severity VARCHAR,
            root_cause_hypothesis TEXT,
            is_diagnosed BOOLEAN DEFAULT FALSE
        )
    """)

    print("[OK] 表结构创建完成")
    return conn


def generate_daily_metrics(conn):
    """生成 daily_metrics 数据"""

    print(f"\n[INFO] 生成 daily_metrics 数据...")
    print(f"   时间范围: {START_DATE.date()} 到 {END_DATE.date()}")
    print(f"   站点数: {len(SITES)}")
    print(f"   品类数: {len(CATEGORIES)}")

    data = []
    current_date = START_DATE
    total_days = (END_DATE - START_DATE).days + 1

    # 为每个站点和品类设置基线指标
    baselines = {}
    for site in SITES:
        for category in CATEGORIES:
            baselines[(site, category)] = {
                'gmv': random.uniform(50000, 500000),
                'impressions': int(random.uniform(100000, 1000000)),
                'ctr': random.uniform(0.015, 0.045),
                'cvr': random.uniform(0.025, 0.075),
                'active_sellers': int(random.uniform(50, 500)),
            }

    day_count = 0

    while current_date <= END_DATE:
        day_count += 1

        # 周末效应（周末流量通常更高）
        is_weekend = current_date.weekday() in [5, 6]
        weekend_multiplier = 1.2 if is_weekend else 1.0

        # 季节性效应（Q4 更高，模拟购物季）
        if current_date.month in [11, 12]:  # Black Friday, Christmas
            seasonal_multiplier = 1.5
        elif current_date.month in [1, 2]:  # 春节
            seasonal_multiplier = 1.3
        else:
            seasonal_multiplier = 1.0

        for site in SITES:
            for category in CATEGORIES:
                baseline = baselines[(site, category)]

                # 基础指标（加入随机波动）
                base_gmv = baseline['gmv'] * random.uniform(0.85, 1.15)
                base_impressions = int(baseline['impressions'] * random.uniform(0.85, 1.15))
                base_ctr = baseline['ctr'] * random.uniform(0.9, 1.1)
                base_cvr = baseline['cvr'] * random.uniform(0.9, 1.1)

                # 应用季节性和周末效应
                base_gmv *= weekend_multiplier * seasonal_multiplier
                base_impressions = int(base_impressions * weekend_multiplier * seasonal_multiplier)

                # 注入异常（5% 概率）
                anomaly_type = None
                if random.random() < ANOMALY_RATE:
                    anomaly_type = random.choice([
                        'traffic_drop',
                        'conversion_drop',
                        'campaign_overlap',
                        'seller_churn',
                        'spike'
                    ])

                    if anomaly_type == 'traffic_drop':
                        # 流量骤降 30-50%
                        base_impressions = int(base_impressions * random.uniform(0.5, 0.7))
                    elif anomaly_type == 'conversion_drop':
                        # 转化率下降 30-40%
                        base_cvr *= random.uniform(0.6, 0.7)
                    elif anomaly_type == 'campaign_overlap':
                        # 促销重叠导致 GMV 虚高但利润率低
                        base_gmv *= 1.3
                        base_cvr *= 1.2
                    elif anomaly_type == 'seller_churn':
                        # 卖家流失
                        baseline['active_sellers'] = int(baseline['active_sellers'] * 0.8)
                    elif anomaly_type == 'spike':
                        # 异常增长（可能是数据错误或营销活动）
                        base_gmv *= random.uniform(1.5, 2.0)

                # 计算衍生指标
                clicks = int(base_impressions * base_ctr)
                orders = int(clicks * base_cvr)
                sold_items = int(orders * random.uniform(1.1, 1.5))
                asp = base_gmv / sold_items if sold_items > 0 else 0

                data.append({
                    'date': current_date.strftime('%Y-%m-%d'),
                    'site': site,
                    'category': category,
                    'gmv': round(base_gmv, 2),
                    'sold_items': sold_items,
                    'impressions': base_impressions,
                    'clicks': clicks,
                    'orders': orders,
                    'ctr': round(base_ctr, 4),
                    'cvr': round(base_cvr, 4),
                    'asp': round(asp, 2),
                    'active_sellers': baseline['active_sellers'],
                    'new_listings': int(random.uniform(100, 1000))
                })

        current_date += timedelta(days=1)

        # 进度显示
        if day_count % 30 == 0:
            progress = (day_count / total_days) * 100
            print(f"   进度: {progress:.1f}% ({len(data):,} 行)")

    # 批量插入
    print(f"   [INFO] 插入数据到数据库...")
    conn.executemany("""
        INSERT INTO daily_metrics VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        d['date'], d['site'], d['category'], d['gmv'], d['sold_items'],
        d['impressions'], d['clicks'], d['orders'], d['ctr'], d['cvr'],
        d['asp'], d['active_sellers'], d['new_listings']
    ) for d in data])

    # 创建索引
    print("   [INFO] 创建索引...")
    conn.execute("CREATE INDEX idx_date ON daily_metrics(date)")
    conn.execute("CREATE INDEX idx_site_category ON daily_metrics(site, category)")

    print(f"[OK] daily_metrics 生成完成: {len(data):,} 行")
    return len(data)


def generate_campaigns(conn):
    """生成 campaigns 数据"""

    print(f"\n[INFO] 生成 campaigns 数据...")

    campaigns = []
    campaign_names = [
        'Black Friday 2025',
        'Cyber Monday 2025',
        'Christmas Sale 2025',
        'New Year Deals 2026',
        'Spring Festival 2026',
        'Valentine Special 2026',
        'Easter Sale 2026',
        'Summer Blast 2026',
        'Back to School 2026',
        'Halloween Special 2026',
        'Black Friday 2026',
        'Year End Clearance 2026'
    ]

    campaign_dates = [
        ('2025-11-25', '2025-11-28'),  # Black Friday
        ('2025-11-29', '2025-12-01'),  # Cyber Monday
        ('2025-12-15', '2025-12-25'),  # Christmas
        ('2026-01-01', '2026-01-07'),  # New Year
        ('2026-02-10', '2026-02-17'),  # Spring Festival
        ('2026-02-12', '2026-02-16'),  # Valentine
        ('2026-04-10', '2026-04-20'),  # Easter
        ('2026-06-15', '2026-06-30'),  # Summer
        ('2026-08-15', '2026-09-05'),  # Back to School
        ('2026-10-25', '2026-10-31'),  # Halloween
        ('2026-11-25', '2026-11-28'),  # Black Friday
        ('2026-12-20', '2026-12-31'),  # Year End
    ]

    for i, (name, (start, end)) in enumerate(zip(campaign_names, campaign_dates)):
        for site in random.sample(SITES, k=random.randint(3, 6)):
            campaign_id = f"CAMP_{i+1:03d}_{site}"
            category = random.choice(CATEGORIES + [None])  # None = all categories

            discount = random.uniform(0.10, 0.30)  # 10-30% off
            subsidy = random.uniform(10000, 100000)
            target_gmv = subsidy / discount * random.uniform(8, 15)
            actual_gmv = target_gmv * random.uniform(0.7, 1.3)
            roi = (actual_gmv - subsidy) / subsidy if subsidy > 0 else 0

            campaigns.append({
                'campaign_id': campaign_id,
                'campaign_name': name,
                'site': site,
                'category': category,
                'start_date': start,
                'end_date': end,
                'discount_rate': round(discount, 2),
                'subsidy_budget': round(subsidy, 2),
                'target_gmv': round(target_gmv, 2),
                'actual_gmv': round(actual_gmv, 2),
                'roi': round(roi, 2)
            })

    # 插入数据
    conn.executemany("""
        INSERT INTO campaigns VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, [(
        c['campaign_id'], c['campaign_name'], c['site'], c['category'],
        c['start_date'], c['end_date'], c['discount_rate'],
        c['subsidy_budget'], c['target_gmv'], c['actual_gmv'], c['roi']
    ) for c in campaigns])

    print(f"[OK] campaigns 生成完成: {len(campaigns)} 个活动")
    return len(campaigns)


def generate_sellers(conn):
    """生成 sellers 数据"""

    print(f"\n[INFO] 生成 sellers 数据...")

    sellers = []
    seller_count = 500

    countries = ['US', 'CN', 'UK', 'DE', 'AU', 'JP', 'FR', 'CA', 'IT', 'ES']

    for i in range(seller_count):
        seller_id = f"SELLER_{i+1:05d}"
        site = random.choice(SITES)
        country = random.choice(countries)

        # 随机加入日期
        days_ago = random.randint(30, 730)
        join_date = END_DATE - timedelta(days=days_ago)

        # 最后上架日期
        days_since_listing = random.randint(0, 30)
        last_listing = END_DATE - timedelta(days=days_since_listing)

        # 状态：90% active, 5% suspended, 5% churned
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
            'is_top_rated': random.random() < 0.2,  # 20% 是 top rated
            'status': status,
            'last_listing_date': last_listing.strftime('%Y-%m-%d')
        })

    # 插入数据
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
    print(f"daily_metrics:  {result[0]:,} 行")

    # 日期范围
    result = conn.execute("SELECT MIN(date), MAX(date) FROM daily_metrics").fetchone()
    print(f"  日期范围:     {result[0]} 到 {result[1]}")

    # 站点数
    result = conn.execute("SELECT COUNT(DISTINCT site) FROM daily_metrics").fetchone()
    print(f"  站点数:       {result[0]}")

    # 品类数
    result = conn.execute("SELECT COUNT(DISTINCT category) FROM daily_metrics").fetchone()
    print(f"  品类数:       {result[0]}")

    # 总 GMV
    result = conn.execute("SELECT SUM(gmv) FROM daily_metrics").fetchone()
    print(f"  总 GMV:       ${result[0]:,.2f}")

    # campaigns 统计
    result = conn.execute("SELECT COUNT(*) FROM campaigns").fetchone()
    print(f"\ncampaigns:      {result[0]} 个活动")

    # sellers 统计
    result = conn.execute("SELECT COUNT(*) FROM sellers").fetchone()
    print(f"sellers:        {result[0]} 个卖家")

    # 示例查询：德国站 Electronics 品类的平均 GMV
    print("\n" + "-"*60)
    print("[EXAMPLE] 示例查询：德国站 Electronics 最近 7 天 GMV")
    print("-"*60)

    result = conn.execute("""
        SELECT date, gmv, sold_items
        FROM daily_metrics
        WHERE site = 'DE' AND category = 'Electronics'
        ORDER BY date DESC
        LIMIT 7
    """).fetchall()

    for row in result:
        print(f"  {row[0]}: ${row[1]:,.2f} ({row[2]:,} items)")

    print("="*60)


def main():
    """主函数"""

    print("="*60)
    print("SignalPilot 数据生成器")
    print("="*60)

    try:
        # 创建数据库
        conn = create_database()

        # 生成数据
        generate_daily_metrics(conn)
        generate_campaigns(conn)
        generate_sellers(conn)

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
