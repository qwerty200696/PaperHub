#!/usr/bin/env python3
import requests
from bs4 import BeautifulSoup
from pathlib import Path
import re
import urllib.parse

test_url = "https://thariqs.github.io/html-effectiveness/"

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
}

print("=" * 80)
print(f"正在获取网页: {test_url}")
print("=" * 80)

resp = requests.get(test_url, headers=headers, timeout=30)
resp.encoding = resp.apparent_encoding
html = resp.text

print(f"✅ 成功获取网页，大小: {len(html)} 字节")

# 完整保存网页
save_dir = Path(__file__).parent / "data" / "saved_web_pages"
save_dir.mkdir(parents=True, exist_ok=True)
parsed = urllib.parse.urlparse(test_url)
safe_name = re.sub(r'[^\w\-.]', '_', parsed.netloc + parsed.path)
if not safe_name.endswith('.html'):
    safe_name += '.html'
full_path = save_dir / safe_name

with open(full_path, 'w', encoding='utf-8') as f:
    f.write(html)
print(f"💾 完整网页已保存到: {full_path}")

# 提取正文
print("\n" + "=" * 80)
print("提取正文...")
print("=" * 80)
soup = BeautifulSoup(html, 'lxml')

# 移除无用标签
for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe', 'noscript']):
    tag.decompose()

title_tag = soup.find('title')
title = title_tag.get_text(strip=True) if title_tag else '无标题'
print(f"📌 标题: {title}")

# 获取所有段落
paragraphs = soup.find_all('p')
main_content = []
for p in paragraphs:
    text = p.get_text(strip=False).strip()
    if len(text) > 30:
        main_content.append(text)

final_text = '\n\n'.join(main_content)
print(f"📝 正文长度: {len(final_text)} 字符")

print("\n" + "=" * 80)
print("正文预览：")
print("=" * 80)
preview = final_text[:2000]
print(preview)
if len(final_text) > 2000:
    print("\n... (内容截断)")

text_file = full_path.with_suffix('.txt')
with open(text_file, 'w', encoding='utf-8') as f:
    f.write(f"标题: {title}\n\n")
    f.write(final_text)
print(f"\n📄 纯文本正文也保存到: {text_file}")
print("\n🎉 测试成功完成！")
