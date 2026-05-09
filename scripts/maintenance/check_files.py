#!/usr/bin/env python3
import sqlite3
from pathlib import Path

def table_has_column(cursor, table_name, column_name):
    cursor.execute(f'PRAGMA table_info({table_name})')
    columns = [row[1] for row in cursor.fetchall()]
    return column_name in columns

db_path = Path(__file__).parent.parent.parent / 'data' / 'db' / 'paperhub.db'
data_dir = Path(__file__).parent.parent.parent / 'data'

conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 100)
print("📁 数据库文件完整性检查")
print("=" * 100)

tables_config = [
    ('papers', '论文'),
    ('articles', '文章'),
    ('notes', '笔记'),
]

total_checked = 0
total_missing = 0

for table, label in tables_config:
    print(f"\n📋 {label}表 ({table}):")
    print("-" * 100)
    
    has_file_path = table_has_column(cursor, table, 'file_path')
    if not has_file_path:
        print(f"  ⏭️  该表没有 file_path 字段，跳过")
        continue
    
    cursor.execute(f'SELECT id, title, file_path FROM {table}')
    rows = cursor.fetchall()
    
    print(f"  {'ID':<4} {'标题':<42} {'状态':<6} {'文件路径':<50}")
    print("-" * 100)
    
    table_missing = 0
    for row_id, title, file_path in rows:
        total_checked += 1
        file_exists = '✅'
        if file_path:
            fp = Path(file_path)
            if not fp.is_absolute():
                if str(fp).startswith('data/'):
                    fp = Path(__file__).parent.parent.parent / fp
                else:
                    fp = data_dir / fp
            if not fp.exists():
                file_exists = '❌'
                table_missing += 1
                total_missing += 1
        else:
            file_exists = '—'
        
        safe_title = str(title)[:40].ljust(40)
        safe_path = (str(file_path) or 'None')[:48].ljust(48)
        print(f"  {row_id:<4} {safe_title:<42} {file_exists:<6} {safe_path}")
    
    print(f"\n  本表总计: {len(rows)} 条记录, 缺失文件: {table_missing} 个")

print("\n" + "=" * 100)
print(f"📊 总体统计:")
print(f"   总计检查: {total_checked} 条记录")
print(f"   文件缺失: {total_missing} 个")
if total_missing == 0:
    print(f"   ✅ 所有文件都存在！")
print("=" * 100)

conn.close()
