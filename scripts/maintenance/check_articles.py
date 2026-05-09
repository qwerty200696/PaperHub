#!/usr/bin/env python3
"""检查已导入的微信文章"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from backend.models import Article
except ImportError:
    from models import Article

try:
    from backend.config import get_session
except ImportError:
    from config import get_session

session = get_session()

print("=== 已导入的微信文章 ===")
articles = session.query(Article).filter(Article.is_deleted == False).order_by(Article.id.desc()).all()

for article in articles:
    print(f"ID: {article.id}")
    print(f"标题: {article.title}")
    print(f"账号: {article.author}")
    print(f"URL: {article.url}")
    print(f"创建时间: {article.created_at}")
    print(f"发布时间: {article.published_at}")
    print(f"文件路径: {article.file_path}")
    print("-" * 60)

print(f"\n总计: {len(articles)} 篇文章")
session.close()
