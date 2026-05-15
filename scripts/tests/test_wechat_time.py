#!/usr/bin/env python3
"""
对比测试微信公众号文章新旧两个抓取函数的发布时间提取
"""
import sys
from pathlib import Path

backend_path = Path(__file__).resolve().parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.wechat_parser import fetch_wechat_article, fetch_wechat_article_new

TEST_URL = "https://mp.weixin.qq.com/s/M7cG_SohZn46uIiowOgykw"

print("=" * 80)
print("📱 微信公众号文章抓取时间对比测试")
print("=" * 80)
print(f"测试文章: {TEST_URL}")
print()

print("👉  1. 测试旧函数 fetch_wechat_article (直接爬取原始页面)")
print("-" * 80)
try:
    result_old = fetch_wechat_article(TEST_URL, extract_content_only=True)
    print(f"  ✅ 成功")
    print(f"  标题: {result_old.get('title')}")
    print(f"  公众号: {result_old.get('account_name')}")
    print(f"  发布日期: {result_old.get('published_at')}")
    print(f"  内容长度: {len(result_old.get('content', ''))}")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("👉  2. 测试新函数 fetch_wechat_article_new (第三方API)")
print("-" * 80)
try:
    result_new = fetch_wechat_article_new(TEST_URL, format='html')
    if result_new:
        print(f"  ✅ 成功")
        print(f"  标题: {result_new.get('title')}")
        print(f"  公众号: {result_new.get('account_name')}")
        print(f"  发布日期: {result_new.get('published_at')}")
        print(f"  内容长度: {len(result_new.get('content', ''))}")
    else:
        print(f"  ❌ 返回 None")
except Exception as e:
    print(f"  ❌ 失败: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("✅ 对比测试完成")
print("=" * 80)
