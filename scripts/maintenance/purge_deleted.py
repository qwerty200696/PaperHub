#!/usr/bin/env python3
import sqlite3
from pathlib import Path
import sys

def table_has_column(cursor, table_name, column_name):
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

db_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'db' / 'paperhub.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 70)
print("🗑️  数据库软删记录永久删除工具")
print("=" * 70)

tables = ['notes', 'articles']
to_delete = {}

print("\n📋 扫描可永久删除的软删记录...")
print("-" * 70)

total_count = 0
for table in tables:
    has_is_deleted = table_has_column(cursor, table, 'is_deleted')
    if not has_is_deleted:
        print(f"  ⏭️  表 {table}: 没有 is_deleted 字段，跳过")
        continue
    
    cursor.execute(f'SELECT id, title FROM {table} WHERE is_deleted = 1')
    rows = cursor.fetchall()
    if rows:
        to_delete[table] = rows
        total_count += len(rows)
        print(f"  📋 表 {table}: 发现 {len(rows)} 条软删记录")
        for idx, (row_id, title) in enumerate(rows, 1):
            print(f"     {idx}. ID {row_id}: {str(title)[:60]}...")
    else:
        print(f"  ✅ 表 {table}: 没有软删记录")

if total_count == 0:
    print("\n🎉 没有需要永久删除的记录，退出。")
    conn.close()
    sys.exit(0)

print(f"\n⚠️  总计将永久删除 {total_count} 条记录!")
print("=" * 70)

confirm = input("\n⚠️  确认要永久删除这些记录吗？输入 'YES' 继续，其他任何内容取消操作: ").strip()
if confirm != 'YES':
    print("\n❌ 操作已取消。")
    conn.close()
    sys.exit(0)

print("\n🚀 开始永久删除...")
deleted_count = 0

try:
    for table, rows in to_delete.items():
        ids_to_del = [r[0] for r in rows]
        placeholders = ','.join('?' * len(ids_to_del))
        cursor.execute(f'DELETE FROM {table} WHERE id IN ({placeholders})', ids_to_del)
        deleted_count += cursor.rowcount
        print(f"  ✅ 从表 {table} 删除了 {cursor.rowcount} 条记录")
    
    conn.commit()
    print("\n" + "=" * 70)
    print(f"✅ 操作完成! 共永久删除 {deleted_count} 条记录")
    print("=" * 70)
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ 删除出错: {e}")
    print("  已回滚所有更改")
finally:
    conn.close()
