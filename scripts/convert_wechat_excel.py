#!/usr/bin/env python3
"""
Excel转TXT脚本 - 将微信公众号文章Excel转换为TXT格式
每行一个JSON，按发布时间倒序排列
同时下载封面图片到本地并压缩
"""
import pandas as pd
import json
import requests
import hashlib
from pathlib import Path
from urllib.parse import urlparse
from io import BytesIO

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False
    print("警告: Pillow 未安装，图片将不会被压缩")
    print("安装命令: pip install Pillow")

EXCEL_PATH = '/Users/wanglijie/Documents/wechat_article/宝玉AI.xlsx'
OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'papers' / 'wechat_subscriptions'
OUTPUT_FILE = OUTPUT_DIR / '宝玉AI.txt'
IMAGES_DIR = OUTPUT_DIR / 'images'

# 图片压缩配置
MAX_WIDTH = 240      # 前端展示120px，2倍图足够清晰
MAX_HEIGHT = 160     # 前端展示80px，2倍图足够清晰
JPEG_QUALITY = 75    # JPEG压缩质量


def compress_image(image_data, save_path):
    """压缩图片到合适尺寸"""
    if not HAS_PIL:
        # 没有Pillow，直接保存原图
        with open(save_path, 'wb') as f:
            f.write(image_data)
        return True

    try:
        img = Image.open(BytesIO(image_data))

        # 转换为RGB（处理RGBA、P模式等）
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # 等比例缩放
        original_width, original_height = img.size
        ratio = min(MAX_WIDTH / original_width, MAX_HEIGHT / original_height, 1.0)

        if ratio < 1.0:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # 保存为JPEG
        save_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(save_path, 'JPEG', quality=JPEG_QUALITY, optimize=True)
        return True

    except Exception as e:
        print(f"  压缩失败: {e}，尝试保存原图")
        try:
            with open(save_path, 'wb') as f:
                f.write(image_data)
            return True
        except Exception:
            return False


def download_image(url, save_path):
    """下载图片并压缩"""
    if not url or pd.isna(url):
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return compress_image(resp.content, save_path)
    except Exception as e:
        print(f"  下载失败: {url[:60]}... - {e}")
    return False


def get_image_filename(url):
    """根据URL生成图片文件名"""
    # 使用URL的MD5作为文件名，避免特殊字符问题
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
    # 统一使用.jpg扩展名（因为压缩后都是JPEG）
    return f"{url_hash}.jpg"


def convert_excel_to_txt():
    # 读取Excel
    print(f"正在读取Excel文件: {EXCEL_PATH}")
    df = pd.read_excel(EXCEL_PATH)

    print(f"共 {len(df)} 条记录")
    if HAS_PIL:
        print(f"图片压缩配置: 最大尺寸 {MAX_WIDTH}x{MAX_HEIGHT}, JPEG质量 {JPEG_QUALITY}")
    else:
        print("Pillow 未安装，将保存原图")

    # 处理发布时间，转为字符串格式
    def format_datetime(dt):
        if pd.isna(dt):
            return ''
        if hasattr(dt, 'strftime'):
            return dt.strftime('%Y-%m-%d %H:%M:%S')
        return str(dt)

    # 按发布时间倒序排列（新的在前）
    df = df.sort_values(by='发布时间', ascending=False)

    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)

    # 提取所需字段，每行一个JSON
    articles = []
    downloaded = 0
    failed = 0
    skipped = 0
    total_original_size = 0
    total_compressed_size = 0

    for idx, row in df.iterrows():
        cover_url = str(row.get('封面', '')) if pd.notna(row.get('封面')) else ''

        # 处理封面图片
        local_cover = ''
        if cover_url and cover_url.startswith('http'):
            img_filename = get_image_filename(cover_url)
            img_path = IMAGES_DIR / img_filename

            if img_path.exists():
                # 已存在，直接使用
                local_cover = f'/static/wechat_subscriptions/images/{img_filename}'
                skipped += 1
            else:
                # 下载并压缩图片
                if download_image(cover_url, img_path):
                    local_cover = f'/static/wechat_subscriptions/images/{img_filename}'
                    downloaded += 1
                    if downloaded % 10 == 0:
                        print(f"  已处理 {downloaded} 张图片...")
                else:
                    # 下载失败，保留原URL
                    local_cover = cover_url
                    failed += 1

        article = {
            'publish_time': format_datetime(row.get('发布时间')),
            'id': str(row.get('ID', '')),
            'title': str(row.get('标题', '')) if pd.notna(row.get('标题')) else '',
            'url': str(row.get('链接', '')) if pd.notna(row.get('链接')) else '',
            'summary': str(row.get('摘要', '')) if pd.notna(row.get('摘要')) else '',
            'cover': local_cover
        }
        articles.append(article)

    # 写入TXT文件，每行一个JSON
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        for article in articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')

    # 统计图片大小
    if IMAGES_DIR.exists():
        total_size = sum(f.stat().st_size for f in IMAGES_DIR.iterdir() if f.is_file())
        print(f"\n图片目录总大小: {total_size / 1024 / 1024:.1f} MB")

    print(f"\n转换完成！共 {len(articles)} 条记录")
    print(f"图片处理: {downloaded} 成功, {failed} 失败, {skipped} 已存在")
    print(f"输出文件: {OUTPUT_FILE}")
    print(f"图片目录: {IMAGES_DIR}")

    # 显示前3条预览
    print("\n前3条记录预览:")
    for i, article in enumerate(articles[:3]):
        print(f"\n--- 记录 {i+1} ---")
        print(f"  标题: {article['title'][:50]}...")
        print(f"  发布时间: {article['publish_time']}")
        print(f"  封面: {article['cover'][:60]}...")


if __name__ == '__main__':
    convert_excel_to_txt()
