"""
验证 generate_data_v2.py 生成的数据质量
"""

import duckdb
from pathlib import Path

def validate_data():
    """验证数据完整性和业务逻辑"""

    db_path = Path(__file__).parent / 'signal.db'

    if not db_path.exists():
        print("[ERROR] 数据库文件不存在，请先运行 generate_data_v2.py")
        return

    conn = duckdb.connect(str(db_path))

    print("="*60)
    print("数据验证报告")
    print("="*60)

    # 1. 基础统计
    print("\n[1] 基础统计")
    print("-"*60)

    tables = ['daily_metrics', 'inventory_daily', 'seller_daily_metrics', 'campaigns', 'sellers']
    for table in tables:
        count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        print(f"{table:25s}: {count:>10,} 行")

    # 2. 日期范围检查
    print("\n[2] 日期范围检查")
    print("-"*60)

    result = conn.execute("""
        SELECT
            MIN(date) as min_date,
            MAX(date) as max_date,
            COUNT(DISTINCT date) as unique_days
        FROM daily_metrics
    """).fetchone()

    print(f"最早日期: {result[0]}")
    print(f"最晚日期: {result[1]}")
    print(f"唯一天数: {result[2]}")
    print(f"预期天数: 913 天 (2024-01-01 到 2026-07-12)")

    # 3. 分类统计
    print("\n[3] 分类统计")
    print("-"*60)

    result = conn.execute("""
        SELECT
            COUNT(DISTINCT category_id_l1) as l1_count,
            COUNT(DISTINCT category_id_l2) as l2_count,
            COUNT(DISTINCT site) as site_count
        FROM daily_metrics
    """).fetchone()

    print(f"L1 分类数: {result[0]} (预期 20)")
    print(f"L2 分类数: {result[1]} (预期 81)")
    print(f"站点数: {result[2]} (预期 10)")

    # 4. 验证 GMV = ASP × Sold Items
    print("\n[4] 验证 GMV = ASP × Sold Items")
    print("-"*60)

    result = conn.execute("""
        SELECT
            COUNT(*) as total_rows,
            SUM(CASE WHEN ABS(gmv - (asp * sold_items)) > 1 THEN 1 ELSE 0 END) as invalid_rows,
            MAX(ABS(gmv - (asp * sold_items))) as max_diff
        FROM daily_metrics
        WHERE sold_items > 0
    """).fetchone()

    print(f"总行数: {result[0]:,}")
    print(f"不一致行数: {result[1]:,}")
    print(f"最大差异: ${result[2]:.2f}")

    if result[1] == 0:
        print("✓ GMV 计算逻辑正确")
    else:
        print("✗ GMV 计算存在问题")

    # 5. 验证 Top-down 一致性
    print("\n[5] 验证 Seller GMV 汇总 = Daily Metrics GMV")
    print("-"*60)

    result = conn.execute("""
        WITH seller_agg AS (
            SELECT
                date, site, category_id_l2,
                SUM(gmv) as seller_total_gmv
            FROM seller_daily_metrics
            GROUP BY date, site, category_id_l2
        )
        SELECT
            COUNT(*) as total_comparisons,
            SUM(CASE WHEN ABS(dm.gmv - sa.seller_total_gmv) > 0.1 THEN 1 ELSE 0 END) as mismatches,
            MAX(ABS(dm.gmv - sa.seller_total_gmv)) as max_diff,
            AVG(ABS(dm.gmv - sa.seller_total_gmv)) as avg_diff
        FROM daily_metrics dm
        JOIN seller_agg sa
            ON dm.date = sa.date
            AND dm.site = sa.site
            AND dm.category_id_l2 = sa.category_id_l2
    """).fetchone()

    print(f"对比总数: {result[0]:,}")
    print(f"不匹配数: {result[1]:,}")
    print(f"最大差异: ${result[2]:.2f}")
    print(f"平均差异: ${result[3]:.4f}")

    if result[1] == 0:
        print("✓ Top-down 分配逻辑正确")
    else:
        print("✗ Top-down 分配存在问题")

    # 6. STR 范围检查
    print("\n[6] STR (售罄率) 范围检查")
    print("-"*60)

    result = conn.execute("""
        SELECT
            MIN(str) as min_str,
            MAX(str) as max_str,
            AVG(str) as avg_str,
            SUM(CASE WHEN str < 0 OR str > 1 THEN 1 ELSE 0 END) as invalid_count
        FROM daily_metrics
    """).fetchone()

    print(f"最小 STR: {result[0]:.2%}")
    print(f"最大 STR: {result[1]:.2%}")
    print(f"平均 STR: {result[2]:.2%}")
    print(f"异常值数: {result[3]}")

    if result[3] == 0 and result[0] >= 0 and result[1] <= 1:
        print("✓ STR 范围正常")
    else:
        print("✗ STR 范围异常")

    # 7. CTR/CVR 范围检查
    print("\n[7] CTR/CVR 范围检查")
    print("-"*60)

    result = conn.execute("""
        SELECT
            MIN(ctr) as min_ctr, MAX(ctr) as max_ctr,
            MIN(cvr) as min_cvr, MAX(cvr) as max_cvr,
            SUM(CASE WHEN ctr < 0 OR ctr > 1 OR cvr < 0 OR cvr > 1 THEN 1 ELSE 0 END) as invalid
        FROM daily_metrics
    """).fetchone()

    print(f"CTR 范围: {result[0]:.2%} ~ {result[1]:.2%}")
    print(f"CVR 范围: {result[2]:.2%} ~ {result[3]:.2%}")
    print(f"异常值数: {result[4]}")

    if result[4] == 0:
        print("✓ CTR/CVR 范围正常")
    else:
        print("✗ CTR/CVR 范围异常")

    # 8. Inventory Health 分布
    print("\n[8] Inventory Health 分布")
    print("-"*60)

    result = conn.execute("""
        SELECT
            inventory_health,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) as percentage
        FROM inventory_daily
        GROUP BY inventory_health
        ORDER BY count DESC
    """).fetchall()

    for row in result:
        print(f"{row[0]:15s}: {row[1]:>10,} 行 ({row[2]:>5.1f}%)")

    # 9. 示例数据展示
    print("\n[9] 示例数据（US 站 Phones 最近3天）")
    print("-"*60)

    result = conn.execute("""
        SELECT
            date,
            category_l2,
            gmv,
            sold_items,
            live_listings,
            ROUND(str * 100, 2) || '%' as str_pct,
            asp
        FROM daily_metrics
        WHERE site = 'US' AND category_id_l2 = 100101
        ORDER BY date DESC
        LIMIT 3
    """).fetchall()

    for row in result:
        print(f"{row[0]} | {row[1]:10s} | GMV: ${row[2]:>12,.2f} | SI: {row[3]:>6,} | LL: {row[4]:>8,} | STR: {row[5]:>6s} | ASP: ${row[6]:>7,.2f}")

    # 10. 数据库大小
    print("\n[10] 数据库文件大小")
    print("-"*60)

    db_size_mb = db_path.stat().st_size / (1024 * 1024)
    print(f"文件大小: {db_size_mb:.2f} MB")

    print("\n" + "="*60)
    print("[DONE] 验证完成")
    print("="*60)

    conn.close()


if __name__ == "__main__":
    validate_data()
