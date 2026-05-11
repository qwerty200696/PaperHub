#!/usr/bin/env python3
import sys
sys.path.insert(0, '.')

from backend.services.web_parser import UniversalWebParser

url = "https://waytoagi.feishu.cn/wiki/YG0zwalijihRREkgmPzcWRInnUg"

print("=" * 80)
print("调试飞书网页正文提取...")
print("=" * 80)

parser = UniversalWebParser()

try:
    html, final_url = parser.fetch_html(url)
    print(f"✅ 获取成功，URL: {final_url}")
    print(f"✅ HTML 长度: {len(html)}")
    
    print("\n" + "="*80)
    print("检查 HTML 开头部分（前2000字符）:")
    print("="*80)
    print(html[:2000])
    
    print("\n" + "="*80)
    print("逐个测试不同提取方法的结果:")
    print("="*80)
    
    # 测试 trafilatura
    print("\n--- 1. trafilatura ---")
    res_t = parser.extract_with_trafilatura(html, final_url)
    print(f"title: {res_t.get('title', '')}")
    print(f"text length: {len(res_t.get('text', ''))}")
    print(f"text[:500]: {res_t.get('text', '')[:500]}")
    
    # 测试 readability
    print("\n--- 2. readability ---")
    res_r = parser.extract_with_readability(html)
    print(f"title: {res_r.get('title', '')}")
    print(f"text length: {len(res_r.get('text', ''))}")
    print(f"text[:500]: {res_r.get('text', '')[:500]}")
    
    # 测试 newspaper
    print("\n--- 3. newspaper ---")
    res_n = parser.extract_with_newspaper(url)
    print(f"title: {res_n.get('title', '')}")
    print(f"text length: {len(res_n.get('text', ''))}")
    print(f"text[:500]: {res_n.get('text', '')[:500]}")
    
    # 测试 bs4
    print("\n--- 4. bs4 ---")
    res_b = parser.extract_with_bs4(html)
    print(f"title: {res_b.get('title', '')}")
    print(f"text length: {len(res_b.get('text', ''))}")
    print(f"text[:500]: {res_b.get('text', '')[:500]}")
    
    # 整体结果
    print("\n" + "="*80)
    print("整体 extract_article 结果:")
    print("="*80)
    full_res = parser.extract_article(url)
    print(f"best_method: {full_res.get('best_method')}")
    print(f"methods_used: {full_res.get('methods_used')}")
    print(f"text_length: {full_res.get('text_length')}")
    print(f"完整 text: {repr(full_res.get('text'))}")
    
except Exception as e:
    import traceback
    print(f"\n❌ 出错: {e}")
    traceback.print_exc()
