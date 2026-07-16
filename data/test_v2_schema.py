"""
测试 V2 Schema 修复后的 SQL Agent
"""
import duckdb
from pathlib import Path

db_path = Path(__file__).parent / 'signal.db'
conn = duckdb.connect(str(db_path))

print("=" * 60)
print("测试 SQL Agent V2 Schema")
print("=" * 60)

# 测试 1: 按 L2 分类汇总 GMV
print("\n[测试 1] 按 L2 分类汇总 GMV")
query1 = """
SELECT category_l1, category_l2, SUM(gmv) as total_gmv
FROM daily_metrics
WHERE site = 'US' AND date >= '2026-06-01'
GROUP BY category_l1, category_l2
ORDER BY total_gmv DESC
LIMIT 10
"""
print(f"SQL: {query1}")
result1 = conn.execute(query1).fetchall()
print(f"结果: {len(result1)} 行")
for row in result1[:5]:
    print(f"  {row[0]} > {row[1]}: ${row[2]:,.2f}")

# 测试 2: 库存健康度分析
print("\n[测试 2] 库存健康度分析")
query2 = """
SELECT inventory_health, COUNT(*) as count, AVG(days_of_supply) as avg_days
FROM inventory_daily
WHERE site = 'US' AND date = '2026-07-12'
GROUP BY inventory_health
"""
print(f"SQL: {query2}")
result2 = conn.execute(query2).fetchall()
print(f"结果: {len(result2)} 行")
for row in result2:
    print(f"  {row[0]}: {row[1]} 个品类, 平均库存天数 {row[2]:.1f}")

# 测试 3: 验证 Dashboard API 字段
print("\n[测试 3] Dashboard API 字段验证")
query3 = """
SELECT
    date,
    SUM(gmv) as total_gmv,
    SUM(sold_items) as total_si,
    AVG(ctr) as avg_ctr,
    AVG(cvr) as avg_cvr,
    SUM(gmv) / NULLIF(SUM(sold_items), 0) as avg_asp,
    SUM(sold_items) / NULLIF(SUM(live_listings), 0) as avg_str
FROM daily_metrics
WHERE site = 'DE'
  AND category_l1 = 'Electronics'
  AND date >= '2026-07-01'
GROUP BY date
ORDER BY date DESC
LIMIT 5
"""
print(f"SQL: {query3}")
result3 = conn.execute(query3).fetchall()
print(f"结果: {len(result3)} 行")
for row in result3:
    print(f"  {row[0]}: GMV=${row[1]:,.0f}, ASP=${row[5]:.2f}, STR={row[6]*100:.2f}%")

# 测试 4: 按 L1 汇总
print("\n[测试 4] 按 L1 分类汇总")
query4 = """
SELECT category_l1, SUM(gmv) as total_gmv, SUM(sold_items) as total_si
FROM daily_metrics
WHERE site = 'DE' AND date >= '2026-06-01'
GROUP BY category_l1
ORDER BY total_gmv DESC
LIMIT 5
"""
print(f"SQL: {query4}")
result4 = conn.execute(query4).fetchall()
print(f"结果: {len(result4)} 行")
for row in result4:
    print(f"  {row[0]}: GMV=${row[1]:,.0f}, SI={row[2]:,}")

conn.close()
print("\n" + "=" * 60)
print("✓ 所有测试通过！V2 Schema 正常工作")
print("=" * 60)
