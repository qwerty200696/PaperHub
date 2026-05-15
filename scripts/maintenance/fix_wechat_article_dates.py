#!/usr/bin/env python3
"""
修复微信公众号文章的发布时间
重新从原始URL提取正确的发布时间并更新数据库
"""
import sys
import time
from pathlib import Path
from datetime import datetime

# 添加backend路径
backend_path = Path(__file__).resolve().parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import sqlite3
from services.wechat_parser import _extract_published_at_only

def fix_wechat_article_dates():
    """修复所有微信公众号文章的发布时间"""
    
    conn = sqlite3.connect('data/db/paperhub.db')
    cursor = conn.cursor()
    
    # 查询所有微信公众号文章
    cursor.execute('''
        SELECT id, title, url, published_at 
        FROM articles 
        WHERE source = 'wechat' AND url LIKE '%mp.weixin.qq.com%'
        ORDER BY id DESC
    ''')
    
    articles = cursor.fetchall()
    print(f"找到 {len(articles)} 篇微信公众号文章")
    print("=" * 100)
    
    updated_count = 0
    skip_count = 0
    error_count = 0
    
    for article_id, title, url, old_pub_date in articles:
        if not url:
            skip_count += 1
            continue
        
        print(f"\n处理 ID {article_id}: {title[:50]}")
        print(f"  当前发布日期: {old_pub_date}")
        
        try:
            # 重新提取发布时间
            accurate_dt = _extract_published_at_only(url)
            new_pub_date = accurate_dt.date()
            
            # 如果日期不同，则更新
            if str(new_pub_date) != old_pub_date:
                cursor.execute(
                    'UPDATE articles SET published_at = ? WHERE id = ?',
                    (new_pub_date.strftime('%Y-%m-%d'), article_id)
                )
                updated_count += 1
                print(f"  ✅ 更新: {old_pub_date} → {new_pub_date}")
            else:
                skip_count += 1
                print(f"  ⏭️  日期正确，跳过")
                
        except Exception as e:
            error_count += 1
            print(f"  ❌ 失败: {e}")
        
        # 每次请求后加2秒延迟，避免触发微信反爬
        time.sleep(2)
    
    conn.commit()
    conn.close()
    
    print("\n" + "=" * 100)
    print(f"✅ 完成！")
    print(f"   更新: {updated_count} 篇")
    print(f"   跳过: {skip_count} 篇")
    print(f"   失败: {error_count} 篇")
    print("=" * 100)

if __name__ == '__main__':
    print("=" * 100)
    print("🔧 修复微信公众号文章发布时间")
    print("=" * 100)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    fix_wechat_article_dates()
    
    print(f"\n结束时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
