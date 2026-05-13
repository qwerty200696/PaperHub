#!/usr/bin/env python3
"""
Excel转TXT脚本 - 将微信公众号文章Excel转换为TXT格式
支持增量更新：读取现有TXT，合并新Excel数据，去重后按时间倒序排列
同时下载封面图片到本地并压缩

用法：
    python convert_wechat_excel.py                                    # 默认路径，默认公众号"宝玉AI"
    python convert_wechat_excel.py /path/to/new.xlsx                  # 指定Excel路径
    python convert_wechat_excel.py /path/to/new.xlsx --name "新公众号" # 指定公众号名称
    python convert_wechat_excel.py /path/to/new.xlsx --name "新公众号" --full  # 全量更新
"""
import pandas as pd
import json
import requests
import hashlib
import argparse
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

# 默认配置
DEFAULT_EXCEL_PATH = '/Users/wanglijie/Documents/wechat_article/宝玉AI.xlsx'
DEFAULT_SUBSCRIPTION_NAME = '宝玉AI'
BASE_OUTPUT_DIR = Path(__file__).parent.parent / 'data' / 'papers' / 'wechat_subscriptions'

# 图片压缩配置
MAX_WIDTH = 240
MAX_HEIGHT = 160
JPEG_QUALITY = 75


def get_output_paths(subscription_name):
    """根据公众号名称获取输出路径"""
    output_dir = BASE_OUTPUT_DIR
    output_file = output_dir / f'{subscription_name}.txt'
    images_dir = output_dir / 'images'
    return output_dir, output_file, images_dir


def compress_image(image_data, save_path):
    if not HAS_PIL:
        with open(save_path, 'wb') as f:
            f.write(image_data)
        return True

    try:
        img = Image.open(BytesIO(image_data))
        if img.mode in ('RGBA', 'P'):
            img = img.convert('RGB')
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        original_width, original_height = img.size
        ratio = min(MAX_WIDTH / original_width, MAX_HEIGHT / original_height, 1.0)

        if ratio < 1.0:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

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
    if not url or pd.isna(url):
        return None
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Referer': 'https://mp.weixin.qq.com/'
        }
        resp = requests.get(url, headers=headers, timeout=30)
        if resp.status_code == 200:
            return compress_image(resp.content, save_path)
    except Exception as e:
        print(f"  下载失败: {url[:60]}... - {e}")
    return False


def get_image_filename(url):
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:16]
    return f"{url_hash}.jpg"


def format_datetime(dt):
    if pd.isna(dt):
        return ''
    if hasattr(dt, 'strftime'):
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return str(dt)


def process_cover(cover_url, images_dir):
    """处理封面图片，返回本地路径"""
    if not cover_url or pd.isna(cover_url):
        return ''
    if not str(cover_url).startswith('http'):
        return str(cover_url)

    img_filename = get_image_filename(cover_url)
    img_path = images_dir / img_filename

    if img_path.exists():
        return f'/static/wechat_subscriptions/images/{img_filename}'
    else:
        if download_image(cover_url, img_path):
            return f'/static/wechat_subscriptions/images/{img_filename}'
        else:
            return str(cover_url)


def row_to_article(row, images_dir):
    return {
        'publish_time': format_datetime(row.get('发布时间')),
        'id': str(row.get('ID', '')),
        'title': str(row.get('标题', '')) if pd.notna(row.get('标题')) else '',
        'url': str(row.get('链接', '')) if pd.notna(row.get('链接')) else '',
        'summary': str(row.get('摘要', '')) if pd.notna(row.get('摘要')) else '',
        'cover': process_cover(row.get('封面', ''), images_dir)
    }


def load_existing_articles(txt_file):
    articles = {}
    if not txt_file.exists():
        return articles

    with open(txt_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    article = json.loads(line)
                    articles[article['id']] = article
                except json.JSONDecodeError:
                    continue
    return articles


def convert_excel_to_txt(excel_path=None, subscription_name=None, incremental=True):
    excel_path = excel_path or DEFAULT_EXCEL_PATH
    subscription_name = subscription_name or DEFAULT_SUBSCRIPTION_NAME

    # 获取输出路径
    output_dir, output_file, images_dir = get_output_paths(subscription_name)

    print(f"=" * 50)
    print(f"Excel转TXT脚本")
    print(f"=" * 50)
    print(f"公众号名称: {subscription_name}")
    print(f"Excel文件: {excel_path}")
    print(f"增量更新: {'是' if incremental else '否'}")
    print(f"输出文件: {output_file}")
    print(f"图片目录: {images_dir}")
    print()

    df = pd.read_excel(excel_path)
    print(f"Excel共 {len(df)} 条记录")

    output_dir.mkdir(parents=True, exist_ok=True)
    images_dir.mkdir(parents=True, exist_ok=True)

    existing_articles = {}
    if incremental and output_file.exists():
        existing_articles = load_existing_articles(output_file)
        print(f"现有TXT共 {len(existing_articles)} 条记录")

    new_count = 0
    updated_count = 0
    skipped_count = 0

    for idx, row in df.iterrows():
        article_id = str(row.get('ID', ''))
        if not article_id:
            continue

        new_article = row_to_article(row, images_dir)

        if article_id in existing_articles:
            existing = existing_articles[article_id]
            has_update = False

            for field in ['summary', 'cover']:
                if not existing.get(field) and new_article.get(field):
                    existing[field] = new_article[field]
                    has_update = True

            if has_update:
                existing_articles[article_id] = existing
                updated_count += 1
            else:
                skipped_count += 1
        else:
            existing_articles[article_id] = new_article
            new_count += 1
            if new_count % 10 == 0:
                print(f"  已添加 {new_count} 篇新文章...")

    # 按发布时间倒序排列
    sorted_articles = sorted(
        existing_articles.values(),
        key=lambda x: x.get('publish_time', ''),
        reverse=True
    )

    # 写入TXT
    with open(output_file, 'w', encoding='utf-8') as f:
        for article in sorted_articles:
            f.write(json.dumps(article, ensure_ascii=False) + '\n')

    # 统计
    if images_dir.exists():
        total_size = sum(f.stat().st_size for f in images_dir.iterdir() if f.is_file())
        print(f"\n图片目录大小: {total_size / 1024 / 1024:.1f} MB")

    print(f"\n转换完成！")
    print(f"  总文章数: {len(sorted_articles)}")
    print(f"  新增: {new_count}")
    print(f"  更新: {updated_count}")
    print(f"  跳过(已存在): {skipped_count}")
    print(f"  输出文件: {output_file}")

    # 显示最新3条
    print(f"\n最新3条文章:")
    for i, article in enumerate(sorted_articles[:3]):
        print(f"  {i+1}. {article['title'][:40]}... ({article['publish_time']})")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Excel转TXT脚本')
    parser.add_argument('excel_path', nargs='?', default=None, help='Excel文件路径')
    parser.add_argument('--name', default=None, help='公众号名称（默认: 宝玉AI）')
    parser.add_argument('--full', action='store_true', help='全量更新（覆盖现有数据）')
    args = parser.parse_args()

    convert_excel_to_txt(
        excel_path=args.excel_path,
        subscription_name=args.name,
        incremental=not args.full
    )
