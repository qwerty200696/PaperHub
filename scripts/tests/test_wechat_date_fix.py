#!/usr/bin/env python3
"""
测试微信公众号文章发布时间提取修复
"""
import sys
from pathlib import Path

# 添加backend路径
backend_path = Path(__file__).resolve().parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

from services.wechat_parser import _extract_published_at_only
from datetime import datetime

# 测试文章URL（请使用实际的文章URL）
TEST_URLS = [
    "https://mp.weixin.qq.com/s/KbPgXz4gPjIieURsqViadg",  # 期待！上海新一波演唱会定档开票！
]

print("=" * 80)
print("📱 微信公众号文章发布时间提取测试")
print("=" * 80)
print(f"当前时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print()

for url in TEST_URLS:
    print(f"测试URL: {url}")
    print("-" * 80)
    try:
        published_at = _extract_published_at_only(url)
        print(f"✅ 提取成功")
        print(f"   发布日期: {published_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   日期部分: {published_at.date()}")
        
        # 检查是否是今天的日期
        if published_at.date() == datetime.now().date():
            print(f"   ✓ 正确识别为今天发布的文章")
        else:
            print(f"   ⚠️  识别为非今天发布的文章")
    except Exception as e:
        print(f"❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()
    print()

print("=" * 80)
print("✅ 测试完成")
print("=" * 80)
