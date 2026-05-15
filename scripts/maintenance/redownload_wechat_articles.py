#!/usr/bin/env python3
"""
重新下载所有微信公众号文章，补全丢失的 _files 图片文件夹
"""
import sys
import random
import time
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import sqlite3
from services.wechat_parser import fetch_wechat_article_new

db_path = Path(__file__).resolve().parent.parent.parent / 'data' / 'db' / 'paperhub.db'
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("=" * 80)
print("📥 微信公众号文章重新下载补全工具")
print("=" * 80)

cursor.execute('SELECT id, title, url, file_path FROM articles WHERE source = "wechat"')
rows = cursor.fetchall()

print(f"\n发现 {len(rows)} 篇微信公众号文章")
print("-" * 80)

success_count = 0
skip_count = 0
error_count = 0

for art_id, title, url, old_file_path in rows:
    if not url or 'mp.weixin.qq.com' not in url:
        skip_count += 1
        print(f"\n⏭️  跳过 ID {art_id}: 无有效微信链接")
        continue
    
    print(f"\n📄 处理 ID {art_id}: {title[:50]}...")
    
    try:
        result = fetch_wechat_article_new(url, format='html')
        if result:
            new_file_path = result.get('file_path', '')
            if new_file_path:
                cursor.execute('UPDATE articles SET file_path = ? WHERE id = ?', (new_file_path, art_id))
                success_count += 1
                print(f"  ✅ 成功: {new_file_path}")
            else:
                print(f"  ⚠️  返回结果无文件路径")
                success_count += 1
        else:
            error_count += 1
            print(f"  ❌ 失败: 返回 None")
    except Exception as e:
        error_count += 1
        print(f"  ❌ 失败: {e}")
    
    # 随机等待 3-8 秒，防反爬
    wait_sec = random.randint(3, 8)
    print(f"  ⏱️  等待 {wait_sec} 秒...")
    time.sleep(wait_sec)

conn.commit()
print("\n" + "=" * 80)
print(f"✅ 全部完成！成功: {success_count} 篇, 跳过: {skip_count} 篇, 失败: {error_count} 篇")
print("=" * 80)

conn.close()
