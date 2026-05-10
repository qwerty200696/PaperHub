#!/usr/bin/env python3
"""快速测试网页提取功能"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from backend.services.web_parser import UniversalWebParser


def main():
    test_url = "https://thariqs.github.io/html-effectiveness/"
    print(f"🚀 开始测试网页: {test_url}\n")
    
    parser = UniversalWebParser()
    
    print("=" * 80)
    print("步骤1: 提取网页正文...")
    print("=" * 80)
    result = parser.extract_article(test_url)
    
    print(f"✅ 提取成功: {result.get('success')}")
    print(f"📌 标题: {result.get('title', '')}")
    print(f"🏆 最佳算法: {result.get('best_method', '')}")
    print(f"📊 正文长度: {result.get('text_length', 0)} 字符")
    print(f"🔧 使用了方法: {result.get('methods_used', [])}")
    
    if result.get('text'):
        print("\n" + "=" * 80)
        print("📝 提取到的正文预览:")
        print("=" * 80)
        preview = result['text'][:1500]
        print(preview)
        if len(result['text']) > 1500:
            print("\n... (内容已截断)")
    
    print("\n" + "=" * 80)
    print("步骤2: 保存完整网页...")
    print("=" * 80)
    save_dir = Path(__file__).parent / "data" / "saved_web_pages"
    save_result = parser.save_complete_page(test_url, save_dir)
    
    print(f"✅ 保存成功: {save_result.get('success')}")
    if save_result.get('success'):
        print(f"📂 保存路径: {save_result.get('saved_path')}")
        print(f"📦 文件大小: {save_result.get('size_bytes', 0)} 字节")
    
    print("\n🎉 测试完成!")


if __name__ == "__main__":
    main()
