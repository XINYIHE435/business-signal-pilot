import duckdb
import pandas as pd

# 数据库文件路径
DB_PATH = r'D:\git\business-signal-pilot\data\signal.db'

# 连接数据库
conn = duckdb.connect(DB_PATH)

# 获取所有表名
tables = conn.execute("SHOW TABLES").fetchall()
table_names = [t[0] for t in tables]

print("=" * 80)
print(f"数据库: {DB_PATH}")
print(f"共 {len(table_names)} 张表: {', '.join(table_names)}")
print("=" * 80)

# 遍历每张表，显示结构和数据样例
for table_name in table_names:
    print(f"\n{'=' * 80}")
    print(f"📊 表名: {table_name}")
    print('=' * 80)
    
    # 1. 获取总行数
    count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    row_count = count_result[0] if count_result else 0
    print(f"📈 总行数: {row_count:,}")
    
    # 2. 获取表结构（列名和类型）
    schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
    print(f"\n📋 表结构 (列名 | 类型 | 是否可为空):")
    print("-" * 60)
    for col in schema:
        print(f"  {col[0]:<20} | {col[1]:<15} | Nullable: {col[2]}")
    
    # 3. 获取前10行数据样例
    print(f"\n📝 数据样例 (前10行):")
    print("-" * 60)
    df = conn.execute(f"SELECT * FROM {table_name} LIMIT 10").df()
    print(df.to_string(index=False))
    
    # 4. 如果有数值列，显示基本统计信息
    numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
    if numeric_cols:
        print(f"\n📊 数值列基本统计:")
        print("-" * 60)
        print(df[numeric_cols].describe().to_string())

print("\n" + "=" * 80)
print("✅ 所有表信息展示完毕！")
print("=" * 80)

# ============================================================================
# 查看其余三个表的信息（时间范围 + 条目总数）
# ============================================================================
print("\n" + "=" * 80)
print("📊 其余三张表信息汇总")
print("=" * 80)

# 需要查看的表列表（排除 daily_metrics）
other_tables = ['anomalies', 'campaigns', 'sellers']

for table_name in other_tables:
    print(f"\n{'─' * 60}")
    print(f"📋 表名: {table_name}")
    print('─' * 60)
    
    # 1. 总行数
    count_result = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()
    row_count = count_result[0] if count_result else 0
    print(f"📈 总条目数: {row_count:,}")
    
    # 2. 查看表结构
    schema = conn.execute(f"DESCRIBE {table_name}").fetchall()
    print(f"\n📋 表结构:")
    for col in schema:
        print(f"   - {col[0]} ({col[1]})")
    
    # 3. 如果表不为空，查看时间范围（尝试找日期字段）
    if row_count > 0:
        # 先获取所有列名
        columns = [col[0] for col in schema]
        
        # 尝试找可能的日期字段（常见命名：date, created_at, update_time, detection_date 等）
        date_candidates = ['date', 'detection_date', 'created_at', 'update_time', 'event_date', 'start_date', 'end_date']
        date_col = None
        for candidate in date_candidates:
            if candidate in columns:
                date_col = candidate
                break
        
        # 如果没找到标准日期字段，找包含 'date' 或 'time' 的列
        if date_col is None:
            for col in columns:
                if 'date' in col.lower() or 'time' in col.lower():
                    date_col = col
                    break
        
        if date_col:
            # 查询时间范围
            date_range = conn.execute(f"""
                SELECT 
                    MIN({date_col}) AS earliest,
                    MAX({date_col}) AS latest
                FROM {table_name}
            """).fetchone()
            
            if date_range[0] and date_range[1]:
                print(f"\n📅 时间范围:")
                print(f"   - 最早: {date_range[0]}")
                print(f"   - 最晚: {date_range[1]}")
            else:
                print(f"\n📅 时间范围: 无法识别日期（字段 {date_col} 可能为空或非日期类型）")
        else:
            print(f"\n📅 时间范围: 表中未找到日期字段")
        
        # 4. 显示前3行数据样例
        print(f"\n📝 数据样例 (前3行):")
        df_sample = conn.execute(f"SELECT * FROM {table_name} LIMIT 3").df()
        print(df_sample.to_string(index=False))
    else:
        print(f"\n⚠️ 该表为空表，无数据展示")

print("\n" + "=" * 80)
print("✅ 所有表信息展示完毕！")
print("=" * 80)

# 关闭连接
conn.close()