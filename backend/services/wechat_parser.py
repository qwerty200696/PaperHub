"""
WeChat Parser - 微信公众号文章解析器
"""
import re
import json
from datetime import datetime
from urllib.parse import urlparse, quote

import requests
from bs4 import BeautifulSoup

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

# 装饰方块检测配置
DECORATION_BOX_CONFIG = {
    'min_size': 16,
    'max_size': 30,
    'common_colors': [
        'rgb(255, 129, 36)',  # 橙色
        'rgb(255, 107, 107)',  # 红色
        'rgb(75, 175, 79)',    # 绿色
        'rgb(66, 133, 244)',   # 蓝色
        'rgb(156, 39, 176)',   # 紫色
        'rgb(255, 193, 7)',    # 黄色
    ]
}


def is_decoration_box(section):
    """检测是否为装饰方块（小尺寸、纯色背景的方块）
    
    Args:
        section: BeautifulSoup section元素
        
    Returns:
        bool: 是否为装饰方块
    """
    style = section.get('style', '')
    
    # 必须有背景色
    if 'background-color' not in style:
        return False
    
    # 检查尺寸是否在装饰方块范围内
    width_match = re.search(r'width:\s*(\d+)px', style)
    height_match = re.search(r'height:\s*(\d+)px', style)
    
    if not width_match or not height_match:
        return False
    
    width = int(width_match.group(1))
    height = int(height_match.group(1))
    
    # 检查是否为小方块（通常16-30像素）
    if not (DECORATION_BOX_CONFIG['min_size'] <= width <= DECORATION_BOX_CONFIG['max_size'] and
            DECORATION_BOX_CONFIG['min_size'] <= height <= DECORATION_BOX_CONFIG['max_size']):
        return False
    
    # 检查是否为常见装饰颜色（可选，用于更精确的匹配）
    bg_color_match = re.search(r'background-color:\s*([^;]+)', style)
    if bg_color_match:
        bg_color = bg_color_match.group(1).strip()
        # 如果匹配到常见颜色，更可能是装饰方块
        if bg_color in DECORATION_BOX_CONFIG['common_colors']:
            return True
        # 对于其他颜色，检查是否为纯色（没有渐变等）
        if not ('gradient' in bg_color or 'url(' in bg_color):
            return True
    
    return False


def is_local_html_file(file_path):
    """检查是否为本地HTML文件"""
    return file_path.lower().endswith('.html') or file_path.lower().endswith('.htm')


def parse_local_html(html_path, assets_folder=None):
    """解析本地保存的微信公众号HTML文件
    
    Args:
        html_path: HTML文件路径
        assets_folder: 资源文件夹路径（_files文件夹）
    
    Returns:
        同fetch_wechat_article的返回格式
    """
    import shutil
    from pathlib import Path
    
    with open(html_path, 'r', encoding='utf-8', errors='ignore') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    title = ''
    author = ''
    account_name = ''
    published_at = datetime.now()
    ip_location = ''
    
    title_elem = soup.find(id='activity-name') or soup.find(class_='rich_media_title') or soup.find('title')
    if title_elem:
        title = title_elem.get_text(strip=True)
    
    meta_items = []
    for elem in soup.find_all(class_='rich_media_meta'):
        text = elem.get_text(strip=True)
        if text:
            meta_items.append(text)
    
    for text in meta_items:
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})?:?(\d{1,2})?', text)
        if match:
            try:
                y, m, d, h, mi = match.groups()
                h = h or '00'
                mi = mi or '00'
                published_at = datetime.strptime(f'{y}-{int(m):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}', '%Y-%m-%d %H:%M')
            except:
                pass
        elif len(text) <= 6 and not re.search(r'[\d@\.]', text) and len(text) >= 2:
            ip_location = text
    
    account_elem = soup.find(class_='wx_follow_nickname') or soup.find(id='js_name') or soup.find(class_='profile_nickname') or soup.find(class_='rich_media_meta_nickname')
    if account_elem:
        account_name = account_elem.get_text(strip=True)
    
    content_elem = soup.find(id='js_content') or soup.find(class_='rich_media_content') or soup.find('body')
    html_content = ''
    content = ''
    
    if content_elem:
        clean_content(content_elem)
        html_content = str(content_elem)
        content = content_elem.get_text(separator='\n', strip=True)
        content = re.sub(r'\n\s*\n', '\n', content).strip()
    
    article_id = str(abs(hash(title + content[:100])))[:8]
    from config import BASE_DIR
    
    save_path = BASE_DIR / f'data/papers/wechat/{article_id}.html'
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    images_dir = save_path.parent / f'{article_id}_files'
    images_dir.mkdir(exist_ok=True)
    
    if content_elem:
        for i, img in enumerate(content_elem.find_all('img')):
            img_url = img.get('data-src', '') or img.get('src', '')
            
            for attr in ['src', 'data-src', 'data-original-src']:
                if img.has_attr(attr):
                    del img[attr]
            
            local_file = None
            
            if img_url and img_url.startswith('http'):
                try:
                    headers = {'User-Agent': USER_AGENT, 'Referer': 'https://mp.weixin.qq.com/'}
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        ext = '.png'
                        if 'wx_fmt=gif' in img_url or '.gif' in img_url[:100]:
                            ext = '.gif'
                        elif 'wx_fmt=jpeg' in img_url or 'wx_fmt=jpg' in img_url or '.jpg' in img_url[:100] or '.jpeg' in img_url[:100]:
                            ext = '.jpg'
                        local_file = f'{i}{ext}'
                        with open(images_dir / local_file, 'wb') as f:
                            f.write(img_resp.content)
                except Exception as e:
                    pass
            
            if local_file:
                img['src'] = f'./{article_id}_files/{local_file}'
            else:
                img.decompose()
    
    html_content = str(content_elem) if content_elem else ''
    
    with open(save_path, 'w', encoding='utf-8') as f:
        pub_date_str = published_at.strftime('%Y年%m月%d日 %H:%M') if published_at else ''
        location_html = f'<span class="location">{ip_location}</span>' if ip_location else ''
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ max-width: 677px; margin: 0 auto; padding: 20px 16px; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", "Microsoft YaHei", sans-serif; line-height: 1.75; color: #333; background-color: #f4f5f6; }}
        .article-container {{ background: white; padding: 32px; border-radius: 12px; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; }}
        h1 {{ font-size: 22px; font-weight: 700; line-height: 1.4; margin-bottom: 14px; color: #222; }}
        .meta-info {{ font-size: 14px; color: #888; margin-bottom: 32px; display: flex; align-items: center; }}
        .meta-info .account {{ color: #576b95; font-weight: 500; margin-right: 14px; }}
        .meta-info .date {{ color: #b2b2b2; margin-right: 14px; }}
        .meta-info .location {{ color: #969696; }}
        .content {{ font-size: 16px; color: #333; line-height: 1.75; }}
        .content p {{ margin-bottom: 20px; }}
        .content h2, .content h3, .content h4 {{ margin-top: 30px; margin-bottom: 16px; font-weight: 600; color: #222; }}
        
        /* 代码块样式 */
        pre {{ background: #f6f8fa; border-radius: 6px; padding: 16px; overflow-x: auto; margin: 20px 0; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }}
        code {{ background: #f1f3f4; padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; font-size: 14px; }}
        pre code {{ background: transparent; padding: 0; border-radius: 0; display: block; }}
        
        /* 表格样式 */
        .table-container {{ overflow-x: auto; margin: 20px 0; }}
        table {{ width: 100%; min-width: 600px; border-collapse: collapse; font-size: 14px; }}
        th, td {{ border: 1px solid #e0e0e0; padding: 12px 16px; text-align: left; white-space: nowrap; }}
        th {{ background: #fafafa; font-weight: 600; color: #333; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        
        /* 列表样式 */
        ul, ol {{ padding-left: 24px; margin: 16px 0; }}
        li {{ margin-bottom: 8px; }}
        
        /* 引用样式 */
        blockquote {{ border-left: 4px solid #409eff; padding-left: 16px; margin: 16px 0; color: #666; }}
    </style>
</head>
<body>
    <div class="article-container">
        <h1>{title}</h1>
        <div class="meta-info">
            <span class="account">{account_name}</span>
            <span class="date">{pub_date_str}</span>
            {location_html}
        </div>
        <div class="content">
{html_content}
        </div>
    </div>
</body>
</html>
        """)
    
    abstract = content[:500] + '...' if len(content) > 500 else content
    
    return {
        'title': title or Path(html_path).stem,
        'author': author,
        'account_name': account_name or '本地导入',
        'abstract': abstract,
        'content': content[:50000],
        'html_content': html_content,
        'published_at': published_at.date(),
        'source_url': f'file://{html_path}',
        'wechat_id': article_id,
        'source': 'wechat',
        'file_path': f'data/papers/wechat/{article_id}.html'
    }


def is_wechat_url(url):
    """检查是否为微信公众号链接"""
    if not url:
        return False
    parsed = urlparse(url)
    return ('mp.weixin.qq.com' in parsed.netloc and '/s?' in parsed.path) or 'mp.weixin.qq.com/s/' in url


def extract_wechat_id(url):
    """从URL中提取文章ID"""
    parsed = urlparse(url)
    if '/s/' in url:
        match = re.search(r'/s/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
    query = parsed.query
    if '__biz=' in query and 'mid=' in query and 'idx=' in query:
        match = re.search(r'__biz=([a-zA-Z0-9=_-]+).*?mid=(\d+).*?idx=(\d+)', url)
        if match:
            biz, mid, idx = match.groups()
            return f"{biz}_{mid}_{idx}"
    return None


def fetch_wechat_article(url, extract_content_only=False):
    """抓取微信公众号文章内容
    
    Args:
        url: 微信公众号文章链接
        extract_content_only: 是否只提取正文并生成干净HTML，False=保存原始网页+JS修复，True=提取正文生成新HTML
    
    Returns:
        {
            'title': str,
            'author': str,
            'account_name': str,
            'content': str,  # 纯文本内容
            'html_content': str,  # 清理后的HTML
            'published_at': datetime,
            'source_url': url,
            'original': bool
        }
    """
    headers = {
        'User-Agent': USER_AGENT,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8'
    }
    
    response = requests.get(url, headers=headers, timeout=30)
    response.encoding = 'utf-8'
    html = response.text
    
    soup = BeautifulSoup(html, 'lxml')
    
    title = ''
    author = ''
    account_name = ''
    published_at = datetime.now()
    ip_location = ''
    content = ''
    
    title_elem = soup.find(id='activity-name') or soup.find(class_='rich_media_title')
    if title_elem:
        title = title_elem.get_text(strip=True)
    
    if not title:
        title_elem = soup.find('title')
        if title_elem:
            title = title_elem.get_text(strip=True)
            if '微信' in title or '公众号' in title:
                title = title.replace('- 微信公众号', '').replace('微信公众号-', '').strip()
    
    if not title:
        title_elem = soup.find(class_='article-title') or soup.find(class_='title')
        if title_elem:
            title = title_elem.get_text(strip=True)
    
    if not title:
        title_elem = soup.find('h1')
        if title_elem:
            title = title_elem.get_text(strip=True)
    
    meta_items = []
    for elem in soup.find_all(class_='rich_media_meta'):
        text = elem.get_text(strip=True)
        if text:
            meta_items.append(text)
    
    for text in meta_items:
        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})?:?(\d{1,2})?', text)
        if match:
            try:
                y, m, d, h, mi = match.groups()
                h = h or '00'
                mi = mi or '00'
                published_at = datetime.strptime(f'{y}-{int(m):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}', '%Y-%m-%d %H:%M')
            except:
                pass
        elif len(text) <= 6 and not re.search(r'[\d@\.]', text) and len(text) >= 2:
            # 处理重复的位置信息（如"厦大等厦大等"变成"厦大等"）
            # 检测文本是否是重复模式
            if len(text) % 2 == 0:
                half_len = len(text) // 2
                if text[:half_len] == text[half_len:]:
                    text = text[:half_len]
            # 避免重复设置
            if ip_location and text in ip_location:
                continue
            ip_location = text

    if published_at.date() == datetime.now().date():
        timestamps = []
        for match in re.finditer(r'\D(\d{10})\D', html):
            ts = int(match.group(1))
            if 1700000000 < ts < int(datetime.now().timestamp() - 3600):
                timestamps.append(ts)
        if timestamps:
            estimated_ts = sorted(timestamps)[len(timestamps) // 3]
            published_at = datetime.fromtimestamp(estimated_ts)
    
    account_elem = soup.find(class_='wx_follow_nickname') or soup.find(id='js_name')
    if account_elem:
        account_name = account_elem.get_text(strip=True)
    
    content_elem = soup.find(id='js_content') or soup.find(class_='rich_media_content') or soup.find('body')
    content = ''
    
    article_id = extract_wechat_id(url)
    from config import BASE_DIR
    
    save_path = BASE_DIR / f'data/papers/wechat/{article_id}.html'
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    images_dir = save_path.parent / f'{article_id}_files'
    images_dir.mkdir(exist_ok=True)
    
    if content_elem:
        content = content_elem.get_text(separator='\n', strip=True)
        content = re.sub(r'\n\s*\n', '\n', content).strip()
    
    abstract = content[:200] + '...' if len(content) > 200 else content
    html_content = ''
    
    if extract_content_only:
        # 先处理图片（需要在clean_content之前，因为clean_content会删除属性）
        if content_elem:
            for i, img in enumerate(content_elem.find_all('img')):
                img_url = img.get('data-src', '') or img.get('src', '')
                
                local_file = None
                
                if img_url and img_url.startswith('http'):
                    try:
                        headers = {'User-Agent': USER_AGENT, 'Referer': 'https://mp.weixin.qq.com/'}
                        img_resp = requests.get(img_url, headers=headers, timeout=10)
                        if img_resp.status_code == 200:
                            ext = '.png'
                            if 'wx_fmt=gif' in img_url or '.gif' in img_url[:100]:
                                ext = '.gif'
                            elif 'wx_fmt=jpeg' in img_url or 'wx_fmt=jpg' in img_url or '.jpg' in img_url[:100] or '.jpeg' in img_url[:100]:
                                ext = '.jpg'
                            local_file = f'{i}{ext}'
                            with open(images_dir / local_file, 'wb') as f:
                                f.write(img_resp.content)
                    except Exception as e:
                        pass
                
                if local_file:
                    img['src'] = f'./{article_id}_files/{local_file}'
                else:
                    img.decompose()
        
        # 然后清理内容
        if content_elem:
            clean_content(content_elem)
            html_content = str(content_elem)
        
        pub_date_str = published_at.strftime('%Y年%m月%d日 %H:%M') if published_at else ''
        location_html = f'<span class="location">{ip_location}</span>' if ip_location else ''
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ max-width: 677px; margin: 0 auto; padding: 20px 16px; font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", "Microsoft YaHei", sans-serif; line-height: 1.75; color: #333; background-color: #f4f5f6; }}
        .article-container {{ background: white; padding: 32px; border-radius: 12px; }}
        img {{ max-width: 100%; height: auto; display: block; margin: 20px auto; }}
        h1 {{ font-size: 22px; font-weight: 700; line-height: 1.4; margin-bottom: 14px; color: #222; }}
        .meta-info {{ font-size: 14px; color: #888; margin-bottom: 32px; display: flex; align-items: center; }}
        .meta-info .account {{ color: #576b95; font-weight: 500; margin-right: 14px; }}
        .meta-info .date {{ color: #b2b2b2; margin-right: 14px; }}
        .meta-info .location {{ color: #969696; }}
        .content {{ font-size: 16px; color: #333; line-height: 1.75; }}
        .content p {{ margin-bottom: 20px; }}
        .content h2, .content h3, .content h4 {{ margin-top: 30px; margin-bottom: 16px; font-weight: 600; color: #222; }}
        
        /* 代码块样式 */
        pre {{ background: #f6f8fa; border-radius: 6px; padding: 16px; overflow-x: auto; margin: 20px 0; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; font-size: 14px; line-height: 1.6; white-space: pre-wrap; word-wrap: break-word; }}
        code {{ background: #f1f3f4; padding: 2px 6px; border-radius: 4px; font-family: 'SF Mono', 'Monaco', 'Inconsolata', 'Roboto Mono', monospace; font-size: 14px; }}
        pre code {{ background: transparent; padding: 0; border-radius: 0; display: block; }}
        
        /* 表格样式 */
        .table-container {{ overflow-x: auto; margin: 20px 0; }}
        table {{ width: 100%; min-width: 600px; border-collapse: collapse; font-size: 14px; }}
        th, td {{ border: 1px solid #e0e0e0; padding: 12px 16px; text-align: left; white-space: nowrap; }}
        th {{ background: #fafafa; font-weight: 600; color: #333; }}
        tr:nth-child(even) {{ background: #fafafa; }}
        
        /* 列表样式 */
        ul, ol {{ padding-left: 24px; margin: 16px 0; }}
        li {{ margin-bottom: 8px; }}
        
        /* 引用样式 */
        blockquote {{ border-left: 4px solid #409eff; padding-left: 16px; margin: 16px 0; color: #666; }}
    </style>
</head>
<body>
    <div class="article-container">
        <h1>{title}</h1>
        <div class="meta-info">
            <span class="account">{account_name}</span>
            <span class="date">{pub_date_str}</span>
            {location_html}
        </div>
        <div class="content">
{html_content}
        </div>
    </div>
</body>
</html>
            """)
    else:
        for style in soup.find_all('style'):
            style.decompose()
        
        body = soup.find('body')
        if body:
            del body['style']
            body['style'] = 'visibility: visible !important; opacity: 1 !important;'
        
        for i, img in enumerate(soup.find_all('img')):
            img_url = img.get('data-src', '') or img.get('src', '')
            
            for attr in ['srcset', 'data-src', 'data-original-src', 'data-w', 'data-h', 'data-ratio']:
                if img.has_attr(attr):
                    del img[attr]
            
            local_file = None
            
            if img_url and img_url.startswith('http'):
                try:
                    headers = {'User-Agent': USER_AGENT, 'Referer': 'https://mp.weixin.qq.com/'}
                    img_resp = requests.get(img_url, headers=headers, timeout=10)
                    if img_resp.status_code == 200:
                        ext = '.png'
                        if 'wx_fmt=gif' in img_url or '.gif' in img_url[:100]:
                            ext = '.gif'
                        elif 'wx_fmt=jpeg' in img_url or 'wx_fmt=jpg' in img_url or '.jpg' in img_url[:100] or '.jpeg' in img_url[:100]:
                            ext = '.jpg'
                        local_file = f'{i}{ext}'
                        with open(images_dir / local_file, 'wb') as f:
                            f.write(img_resp.content)
                except Exception as e:
                    print(f'Image download failed {img_url[:50]}: {e}')
            
            if local_file:
                img['src'] = f'./{article_id}_files/{local_file}'
            else:
                img.decompose()
        
        extra_style = soup.new_tag('style')
        extra_style.string = '''
            body { background: #f4f5f6 !important; }
            #js_content { visibility: visible !important; }
        '''
        if soup.head:
            soup.head.append(extra_style)
        
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write(str(soup))
    
    return {
        'title': title or '未命名公众号文章',
        'author': author,
        'account_name': account_name or '微信公众号',
        'abstract': abstract,
        'content': content[:50000],
        'html_content': html_content if extract_content_only else content,
        'published_at': published_at.date(),
        'source_url': url,
        'wechat_id': article_id,
        'source': 'wechat',
        'file_path': f'data/papers/wechat/{article_id}.html'
    }


def clean_content(content_elem, remove_styles=True):
    """清理冗余内容和广告
    
    Args:
        content_elem: BeautifulSoup元素
        remove_styles: 是否移除所有内联样式和class属性
    """
    # 微信所有需要移除的属性
    wx_attrs_to_remove = [
        'data-src', 'data-original-src', 'data-w', 'data-h', 'data-ratio',
        'data-index', 'data-type', 'data-fail', 'data-report-img-idx',
        'data-pm-slice', 'data-clipboard-cangjie', 'data-aistatus', 'data-imgfileid', 'data-s',
        'nodeleaf', 'leaf', 'textstyle', '_width', 'srcset',
        'contenteditable', 'typeof', 'property', 'itemscope', 'itemtype'
    ]
    
    # 清理根元素
    if remove_styles:
        if content_elem.has_attr('style'):
            del content_elem['style']
        if content_elem.has_attr('class'):
            del content_elem['class']
    for attr in wx_attrs_to_remove:
        if content_elem.has_attr(attr):
            del content_elem[attr]
    # 删除根元素的id属性
    if content_elem.has_attr('id'):
        del content_elem['id']
    
    to_remove = []
    # 底部栏关键词
    bottom_bar_keywords = ['赞', '分享', '推荐', '写留言', '在看', '喜欢', '收藏', '好看', '转发', '关注', '打赏']
    
    for tag in content_elem.find_all():
        # 有选择性地保留有用的样式
        if remove_styles and tag.has_attr('style'):
            style_str = tag['style']
            # 保留有用的样式属性
            useful_styles = []
            for part in style_str.split(';'):
                part = part.strip()
                if not part:
                    continue
                # 保留文本对齐、加粗、斜体、下划线、颜色、背景色、边框、变换等样式
                if part.startswith('text-align') or \
                   part.startswith('font-weight') or \
                   part.startswith('font-style') or \
                   part.startswith('text-decoration') or \
                   part.startswith('color') or \
                   part.startswith('background-color') or \
                   part.startswith('background') or \
                   part.startswith('width') or \
                   part.startswith('height') or \
                   part.startswith('display') or \
                   part.startswith('vertical-align') or \
                   part.startswith('overflow') or \
                   part.startswith('border') or \
                   part.startswith('transform') or \
                   part.startswith('transform-origin'):
                    useful_styles.append(part)
            if useful_styles:
                tag['style'] = '; '.join(useful_styles)
            else:
                del tag['style']
        
        # 移除class属性
        if remove_styles and tag.has_attr('class'):
            del tag['class']
        
        # 移除其他微信相关属性
        for attr in wx_attrs_to_remove:
            if tag.has_attr(attr):
                del tag[attr]
        
        # 删除所有标签的id属性
        if tag.has_attr('id'):
            del tag['id']
        
        class_text = ' '.join(tag.get('class', []))
        # 使用完整单词匹配，避免子串误判（如 'left' 不应该匹配 'profile'）
        class_words = class_text.lower().split()
        if any(keyword in class_words for keyword in ['ad', 'advertise', 'reward', 'like', 'vote', 'comment', 'follow', 'profile', 'meta', 'copyright']):
            to_remove.append(tag)
            continue
        
        if tag.name == 'script' or tag.name == 'style' or tag.name == 'iframe':
            to_remove.append(tag)
            continue
        
        # 移除空的section标签（微信排版占位）
        if tag.name == 'section' and not tag.get_text(strip=True) and len(tag.find_all()) == 0:
            to_remove.append(tag)
            continue
        
        # 移除svg占位标签
        if tag.name == 'svg' and tag.get('viewbox') == '0 0 1 1':
            to_remove.append(tag)
            continue
        
        text = tag.get_text(strip=True)
        
        # 清理底部栏：短文本中包含多个底部关键词的标签
        # 注意：只有文本较短时才判断为底部栏，避免误删正常文章内容
        # 正常文章内容可能包含"分享"、"关注"等词（如"分享经验"、"关注趋势"）
        bottom_bar_count = sum(1 for kw in bottom_bar_keywords if kw in text)
        if bottom_bar_count >= 2 and len(text) <= 300:
            to_remove.append(tag)
            continue
        
        # 清理单个关键词的小标签（短文本）
        if len(text) <= 20 and any(keyword in text for keyword in ['关注', '点赞', '打赏', '广告', '推荐阅读', '往期', '分享', '赞', '写留言', '在看', '喜欢', '收藏']):
            to_remove.append(tag)
            continue
    
    for tag in to_remove:
        try:
            tag.decompose()
        except:
            pass
    
    # 处理代码块：在<code>标签之间添加换行符
    for pre in content_elem.find_all('pre'):
        code_tags = pre.find_all('code')
        if len(code_tags) > 1:
            for i in range(len(code_tags) - 1):
                code_tags[i].insert_after('\n')
    
    # 处理figure标签：确保图片和图注垂直排列（上下）而不是水平排列（左右）
    for figure in content_elem.find_all('figure'):
        style = figure.get('style', '')
        if 'display: flex' in style:
            # 添加flex-direction: column确保垂直排列
            if 'flex-direction' not in style:
                style += '; flex-direction: column;'
            else:
                style = style.replace('flex-direction: row', 'flex-direction: column')
            figure['style'] = style
    
    # 处理装饰颜色标题：让标题内的p标签变成inline，与装饰方块在同一行显示
    for section in content_elem.find_all('section'):
        style = section.get('style', '')
        # 检查是否为装饰色文字（有颜色但没有背景色）
        has_decoration_color = any(color in style for color in DECORATION_BOX_CONFIG['common_colors'])
        if has_decoration_color and 'color' in style and 'background-color' not in style:
            # 这是装饰色标题（不是装饰方块），让内部p标签变成inline
            for p in section.find_all('p'):
                p_style = p.get('style', '')
                if 'display' not in p_style:
                    p['style'] = 'display: inline;' + p_style

    # 处理嵌套的外层section：确保装饰方块和标题的外层容器都保持inline-block且垂直对齐一致
    for outer_section in content_elem.find_all('section'):
        outer_style = outer_section.get('style', '')
        # 找到包含装饰元素的外层容器（有vertical-align但没有装饰色）
        has_decoration_color = any(color in outer_style for color in DECORATION_BOX_CONFIG['common_colors'])
        if 'vertical-align' in outer_style and not has_decoration_color:
            # 检查是否包含装饰色子元素
            has_decoration_child = False
            for child in outer_section.find_all(['section', 'span']):
                child_style = child.get('style', '')
                if any(color in child_style for color in DECORATION_BOX_CONFIG['common_colors']):
                    has_decoration_child = True
                    break
            if has_decoration_child:
                # 检查是否是居中标题（text-align: center）
                if 'text-align: center' in outer_style:
                    # 居中标题保持原样，不添加display: inline-block
                    continue
                # 非居中的装饰元素容器（装饰方块+标题）：添加display: inline-block，设置vertical-align为top，并禁止换行
                outer_style = outer_style.replace('vertical-align: bottom', 'vertical-align: top')
                if 'display: inline-block' not in outer_style:
                    outer_section['style'] = 'display: inline-block; white-space: nowrap;' + outer_style
                else:
                    # 已有display，添加white-space
                    if 'white-space' not in outer_style:
                        outer_style += '; white-space: nowrap'
                    outer_section['style'] = outer_style
    
    # 统一装饰方块的vertical-align为middle
    for section in content_elem.find_all('section'):
        if is_decoration_box(section):
            # 这是装饰方块 - 使用middle对齐
            style = section.get('style', '')
            style = style.replace('vertical-align: bottom', 'vertical-align: middle')
            style = style.replace('vertical-align: top', 'vertical-align: middle')
            style = style.replace('align-self: flex-start', 'align-self: center')
            section['style'] = style

    # 确保装饰方块的同级元素也使用相同的vertical-align
    for decoration_section in content_elem.find_all('section'):
        if is_decoration_box(decoration_section):
            # 向上遍历找到包含多个section子元素的父容器
            parent = decoration_section.parent
            while parent:
                if parent.name == 'section':
                    parent_style = parent.get('style', '')
                    # 父容器使用flex布局时，设置align-items: center 和 gap: 6px
                    if 'display: flex' in parent_style:
                        parent_style = parent_style.replace('align-items: flex-start', 'align-items: center')
                        parent_style = parent_style.replace('align-items: stretch', 'align-items: center')
                        if 'align-items' not in parent_style:
                            parent_style += '; align-items: center'
                        if 'gap:' not in parent_style:
                            parent_style += '; gap: 6px'
                        parent['style'] = parent_style
                        
                        # 给flex容器内的p标签添加 margin:0
                        p_tags = parent.find_all('p')
                        for p_tag in p_tags:
                            p_style = p_tag.get('style', '')
                            if 'margin' not in p_style:
                                p_style += '; margin:0'
                            else:
                                p_style = p_style.replace('margin:', 'margin:0')
                            p_tag['style'] = p_style
                    
                    children = parent.find_all('section', recursive=False)
                    if len(children) >= 2:
                        # 找到了共同父容器，统一所有子section的vertical-align
                        for child in children:
                            child_style = child.get('style', '')
                            if 'vertical-align' in child_style:
                                child_style = child_style.replace('vertical-align: bottom', 'vertical-align: middle')
                                child_style = child_style.replace('vertical-align: top', 'vertical-align: middle')
                            child['style'] = child_style
                        break
                parent = parent.parent

    # 处理包含装饰元素的同级容器：让它们都变成inline-block
    # 找到所有包含装饰元素的section，让它们的直接父容器变成inline-block
    for decoration_section in content_elem.find_all('section'):
        if is_decoration_box(decoration_section):
            parent = decoration_section.parent
            if parent and parent.name == 'section':
                parent_style = parent.get('style', '')
                if 'text-align' in parent_style and 'display: inline' not in parent_style:
                    parent['style'] = 'display: inline-block; ' + parent_style
    
    # 为表格添加响应式容器
    for table in content_elem.find_all('table'):
        # 创建一个新的BeautifulSoup对象来生成标签
        temp_soup = BeautifulSoup('<div></div>', 'lxml')
        container = temp_soup.find('div')
        container['class'] = 'table-container'
        table.wrap(container)
    
    # 移除空的section标签（可能有嵌套，循环清理多层）
    # 但保留带有背景色的装饰方块（如橙色小方块）
    for _ in range(10):
        for tag in content_elem.find_all('section'):
            # 检查是否有背景色样式（装饰方块）
            style = tag.get('style', '')
            has_background = ('background-color' in style or 'background:' in style)
            if has_background:
                continue  # 保留装饰方块
            # 只有当section完全为空（没有文本且没有任何子标签）时才删除
            if not tag.get_text(strip=True) and len(tag.find_all()) == 0:
                try:
                    tag.decompose()
                except:
                    pass
    
    # 移除空的li标签（微信占位符）
    for li in content_elem.find_all('li'):
        if not li.get_text(strip=True) and len(li.find_all()) == 0:
            try:
                li.decompose()
            except:
                pass
    
    # 简化嵌套的span标签
    for _ in range(3):
        for span in content_elem.find_all('span'):
            children = list(span.children)
            if len(children) == 1 and children[0].name == 'span':
                span.unwrap()
    
    for img in content_elem.find_all('img'):
        data_src = img.get('data-src')
        if data_src:
            img['src'] = data_src
    
    for a in content_elem.find_all('a'):
        a.unwrap()


def save_article_content(article_id, html_content):
    """保存文章HTML到本地"""
    from config import BASE_DIR
    save_path = BASE_DIR / f'data/papers/wechat/{article_id}.html'
    save_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(save_path, 'w', encoding='utf-8') as f:
        f.write(f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ max-width: 800px; margin: 0 auto; padding: 20px; font-family: -apple-system, sans-serif; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
        """)
    
    return f'data/papers/wechat/{article_id}.html'


def fetch_wechat_article_new(url, format='html'):
    """使用新的第三方API抓取微信公众号文章内容

    此接口不需要API密钥

    Args:
        url: 微信公众号文章链接
        format: 输出格式，支持 html / markdown / text / json，默认html

    Returns:
        {
            'title': str,
            'author': str,
            'account_name': str,
            'content': str,
            'html_content': str,
            'published_at': datetime,
            'source_url': url,
            'wechat_id': str,
            'source': 'wechat',
            'file_path': str
        }
    """
    api_url = 'https://down.mptext.top/api/public/v1/download'

    encoded_url = quote(url, safe='')

    params = {
        'url': encoded_url,
        'format': format
    }

    headers = {
        'User-Agent': USER_AGENT,
        'Accept': '*/*'
    }

    try:
        response = requests.get(api_url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'

        if response.status_code == 200:
            article_id = extract_wechat_id(url) or str(abs(hash(url)))[:8]

            from config import BASE_DIR
            save_path = BASE_DIR / f'data/papers/wechat/{article_id}.html'
            save_path.parent.mkdir(parents=True, exist_ok=True)

            if format == 'html':
                html_content = response.text
                soup = BeautifulSoup(html_content, 'lxml')
                
                # 提取发布时间
                published_at = datetime.now()
                
                # 从rich_media_meta中提取时间
                try:
                    for elem in soup.find_all(class_='rich_media_meta'):
                        text = elem.get_text(strip=True)
                        match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日\s*(\d{1,2})?:?(\d{1,2})?', text)
                        if match:
                            try:
                                y, m, d, h, mi = match.groups()
                                h = h or '00'
                                mi = mi or '00'
                                published_at = datetime.strptime(f'{y}-{int(m):02d}-{int(d):02d} {int(h):02d}:{int(mi):02d}', '%Y-%m-%d %H:%M')
                            except:
                                pass
                except Exception as e:
                    print(f"提取时间出错: {e}")
                
                # 如果没找到发布时间，尝试从JS中提取
                try:
                    if published_at.date() == datetime.now().date():
                        timestamps = []
                        for match in re.finditer(r'\D(\d{10})\D', html_content):
                            ts = int(match.group(1))
                            if 1700000000 < ts < int(datetime.now().timestamp() - 3600):
                                timestamps.append(ts)
                        if timestamps:
                            estimated_ts = sorted(timestamps)[len(timestamps) // 3]
                            published_at = datetime.fromtimestamp(estimated_ts)
                except Exception as e:
                    print(f"从JS提取时间出错: {e}")
                
                # 创建图片文件夹
                try:
                    images_dir = save_path.parent / f'{article_id}_files'
                    images_dir.mkdir(exist_ok=True)
                except Exception as e:
                    print(f"创建图片目录出错: {e}")
                    images_dir = None
                
                # 下载并替换图片URL为本地路径
                try:
                    for i, img in enumerate(soup.find_all('img')):
                        img_url = img.get('data-src', '') or img.get('src', '')
                        
                        local_file = None
                        
                        if img_url and img_url.startswith('http') and images_dir:
                            try:
                                img_headers = {'User-Agent': USER_AGENT, 'Referer': 'https://mp.weixin.qq.com/'}
                                img_resp = requests.get(img_url, headers=img_headers, timeout=10)
                                if img_resp.status_code == 200:
                                    ext = '.png'
                                    if 'wx_fmt=gif' in img_url or '.gif' in img_url[:100]:
                                        ext = '.gif'
                                    elif 'wx_fmt=jpeg' in img_url or 'wx_fmt=jpg' in img_url or '.jpg' in img_url[:100] or '.jpeg' in img_url[:100]:
                                        ext = '.jpg'
                                    local_file = f'{i}{ext}'
                                    with open(images_dir / local_file, 'wb') as f:
                                        f.write(img_resp.content)
                            except Exception as e:
                                print(f"下载图片 {i} 出错: {e}")
                        
                        if local_file:
                            img['src'] = f'./{article_id}_files/{local_file}'
                        else:
                            img.decompose()
                except Exception as e:
                    print(f"处理图片出错: {e}")
                
                # 提取标题和账号信息
                try:
                    title_elem = soup.find(id='activity-name') or soup.find(class_='rich_media_title') or soup.find('title')
                    title = title_elem.get_text(strip=True) if title_elem else '未命名公众号文章'

                    account_elem = soup.find(class_='wx_follow_nickname') or soup.find(id='js_name')
                    account_name = account_elem.get_text(strip=True) if account_elem else '微信公众号'
                    
                    content_elem = soup.find(id='js_content') or soup.find(class_='rich_media_content')
                    content = content_elem.get_text(separator='\n', strip=True) if content_elem else ''
                    
                    # 格式化发布时间
                    pub_date_str = published_at.strftime('%Y年%m月%d日 %H:%M') if published_at else ''
                    
                    # 找到公众号名称的父元素，在公众号名称后面添加发布时间
                    if account_elem:
                        date_span = soup.new_tag('span')
                        date_span['style'] = 'color: #b2b2b2; margin-left: 16px; font-size: 14px;'
                        date_span.string = pub_date_str
                        account_elem.insert_after(date_span)
                except Exception as e:
                    print(f"提取文章信息出错: {e}")
                    title = '未命名公众号文章'
                    account_name = '微信公众号'
                    content = ''
                
                # 保存修改后的HTML
                try:
                    html_content = str(soup)
                    with open(save_path, 'w', encoding='utf-8') as f:
                        f.write(html_content)
                except Exception as e:
                    print(f"保存HTML出错: {e}")

                return {
                    'title': title,
                    'author': '',
                    'account_name': account_name,
                    'abstract': content[:200] + '...' if len(content) > 200 else content,
                    'content': content[:50000],
                    'html_content': html_content,
                    'published_at': published_at.date(),
                    'source_url': url,
                    'wechat_id': article_id,
                    'source': 'wechat',
                    'file_path': f'data/papers/wechat/{article_id}.html'
                }
            else:
                result = response.json()
                if result.get('code') == 0:
                    data = result.get('data', {})
                    title = data.get('title', '')
                    author = data.get('author', '')
                    account_name = data.get('account', '')
                    content = data.get('content', '')
                    published_at_str = data.get('publish_time', '')

                    published_at = datetime.now()
                    if published_at_str:
                        try:
                            published_at = datetime.strptime(published_at_str, '%Y-%m-%d %H:%M:%S')
                        except:
                            try:
                                published_at = datetime.strptime(published_at_str, '%Y-%m-%d')
                            except:
                                pass

                    return {
                        'title': title or '未命名公众号文章',
                        'author': author,
                        'account_name': account_name or '微信公众号',
                        'abstract': content[:200] + '...' if len(content) > 200 else content,
                        'content': content[:50000],
                        'html_content': content,
                        'published_at': published_at.date(),
                        'source_url': url,
                        'wechat_id': article_id,
                        'source': 'wechat',
                        'file_path': f'data/papers/wechat/{article_id}.html'
                    }
                else:
                    raise Exception(f"API错误: {result.get('msg', '未知错误')}")
        else:
            raise Exception(f"HTTP错误: {response.status_code}")

    except Exception as e:
        print(f"使用新API获取文章失败: {e}")
        return None
