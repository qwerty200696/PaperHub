#!/usr/bin/env python3
"""
批量修正数据库中所有微信公众号文章的发布日期
"""
import sys
import time
from pathlib import Path

backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import sqlite3
from datetime import datetime
from services.wechat_parser import _extract_published_at_only

db_path = Path(__file__).parent.parent.parent / 'data' / 'db' / 'paperhub.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("🔧 批量修正微信公众号文章发布日期")
print("=" * 80)

cursor.execute('SELECT id, title, url, published_at, file_path, is_deleted, created_at, updated_at FROM articles WHERE source = "wechat"')
rows = cursor.fetchall()

print(f"\n发现 {len(rows)} 篇微信公众号文章")
print(rows)
print("-" * 80)

updated_count = 0
skip_count = 0
error_count = 0

today_str = datetime.now().strftime('%Y-%m-%d')

for art_id, title, url, old_pub_date_str, file_path, is_deleted, created_at, updated_at in rows:
    if not url or 'mp.weixin.qq.com' not in url:
        skip_count += 1
        print(f"⏭️  跳过 ID {art_id}: 无有效微信链接")
        continue
    
    print(f"\n处理 ID {art_id}: {title[:50]}， {url}...")
    
    try:
        accurate_dt = _extract_published_at_only(url)
        new_pub_date = accurate_dt.date()
        
        # 更新到数据库
        cursor.execute('UPDATE articles SET published_at = ? WHERE id = ?', (new_pub_date.strftime('%Y-%m-%d'), art_id))
        updated_count += 1
        old_display = old_pub_date_str or 'None'
        print(f"  ✅ 更新: {old_display} → {new_pub_date}")
    except Exception as e:
        error_count += 1
        print(f"  ❌ 失败: {e}")
    
    # 每次请求后加2秒延迟，避免触发微信反爬
    time.sleep(2)

conn.commit()
print("\n" + "=" * 80)
print(f"✅ 完成！更新: {updated_count} 篇, 跳过: {skip_count} 篇, 失败: {error_count} 篇")
print("=" * 80)

conn.close()
