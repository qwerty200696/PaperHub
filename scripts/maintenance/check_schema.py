#!/usr/bin/env python3
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent.parent.parent / 'data' / 'db' / 'paperhub.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 70)
print("📊 数据库表结构分析")
print("=" * 70)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = [row[0] for row in cursor.fetchall()]

for table in tables:
    print(f"\n📋 表: {table}")
    print("-" * 50)
    cursor.execute(f'PRAGMA table_info({table})')
    columns = cursor.fetchall()
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")

conn.close()
print("\n✅ 完成!")
