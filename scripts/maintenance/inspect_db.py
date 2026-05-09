#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def table_has_column(cursor, table_name, column_name):
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

db_path = Path(__file__).parent.parent.parent / 'data' / 'db' / 'paperhub.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 70)
print("🔍 数据库完整分析报告")
print("=" * 70)

tables = ['notes', 'papers', 'articles']

for table in tables:
    print(f"\n📋 表: {table}")
    print("-" * 50)
    
    has_is_deleted = table_has_column(cursor, table, 'is_deleted')
    
    # 1. 总数（所有记录，含软删）
    cursor.execute(f'SELECT COUNT(*) FROM {table}')
    total = cursor.fetchone()[0]
    
    # 2. 软删数
    deleted = 0
    if has_is_deleted:
        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE is_deleted = 1')
        deleted = cursor.fetchone()[0]
    
    # 3. 活跃数（不含软删，前端展示的数量）
    if has_is_deleted:
        cursor.execute(f'SELECT COUNT(*) FROM {table} WHERE is_deleted = 0 OR is_deleted IS NULL')
        active = cursor.fetchone()[0]
    else:
        active = total
    
    print(f"   总记录数: {total}")
    print(f"   已软删: {deleted}")
    print(f"   活跃记录(前端显示): {active}")
    
    # 如果有软删记录，列出来看看
    if deleted > 0:
        print(f"\n   🗑️  已软删的记录 (前5条):")
        cursor.execute(f'SELECT id, title FROM {table} WHERE is_deleted=1 LIMIT 5')
        for row in cursor.fetchall():
            print(f"     - ID {row[0]}: {row[1][:60]}...")

# 检查重复（在活跃记录里）
print("\n" + "=" * 70)
print("🔍 活跃记录中的重复标题检查")
print("=" * 70)

for table in tables:
    print(f"\n📋 表: {table}")
    has_is_deleted = table_has_column(cursor, table, 'is_deleted')
    
    if has_is_deleted:
        cursor.execute(f'''
            SELECT title, COUNT(*) as cnt 
            FROM {table} 
            WHERE is_deleted = 0 OR is_deleted IS NULL
            GROUP BY title 
            HAVING COUNT(*) > 1 
            ORDER BY cnt DESC
        ''')
    else:
        cursor.execute(f'''
            SELECT title, COUNT(*) as cnt 
            FROM {table} 
            GROUP BY title 
            HAVING COUNT(*) > 1 
            ORDER BY cnt DESC
        ''')
    
    dups = cursor.fetchall()
    if dups:
        print(f"   发现 {len(dups)} 组重复标题:")
        for title, cnt in dups:
            print(f"     x{cnt}: {str(title)[:70]}...")
    else:
        print("   ✅ 没有重复")

conn.close()
print("\n✅ 完成!")
