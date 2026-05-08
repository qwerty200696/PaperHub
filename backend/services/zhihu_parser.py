import re
import time
import hashlib
import shutil
from datetime import datetime
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

from config import BASE_DIR


class ZhihuConverter(MarkdownConverter):
    def convert_img(self, el, text, parent_tags=None):
        src = el.get("src", "")
        if not src:
            return ""
        return f"![image]({src})"

    def convert_span(self, el, text, parent_tags=None):
        if "math-tex" in el.get("class", []):
            return text
        return text

    def convert_pre(self, el, text, parent_tags=None):
        code = el.find("code")
        if code:
            lang = code.get("class", [""])[0]
            lang = lang.replace("language-", "")
            return f"``` {lang}\n{code.get_text()}\n```\n\n"
        return f"```\n{text}\n```\n\n"


def parse_publish_time(time_str):
    """解析知乎发布时间字符串"""
    time_str = re.sub(r"发布于|编辑于", "", time_str).strip()
    try:
        if re.match(r"\d{4}-\d{2}-\d{2}", time_str):
            return datetime.strptime(time_str[:10], "%Y-%m-%d")
        if re.match(r"\d{4}年\d{1,2}月\d{1,2}日", time_str):
            return datetime.strptime(re.search(r"\d{4}年\d{1,2}月\d{1,2}日", time_str).group(), "%Y年%m月%d日")
    except:
        pass
    return datetime.now()


def generate_article_id(title, content):
    content_hash = hashlib.md5((title + content[:500]).encode("utf-8")).hexdigest()[:12]
    return f"zhihu_{content_hash}"


def fetch_zhihu_article(url, cookie_str):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Cookie": cookie_str,
        "Referer": "https://www.zhihu.com/",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    }

    session = requests.Session()
    session.headers.update(headers)

    for i in range(3):
        try:
            resp = session.get(url, timeout=15)
            if resp.status_code == 403:
                raise Exception("403 禁止访问，请更新 Cookie")
            if resp.status_code == 404:
                raise Exception("404 链接不存在，请检查URL")
            resp.raise_for_status()
            return resp.text, session
        except Exception as e:
            if i == 2:
                raise
            time.sleep(1)


def parse_zhihu_html(html):
    soup = BeautifulSoup(html, "html.parser")

    title_el = soup.find("h1")
    title = title_el.get_text(strip=True) if title_el else "未命名文章"

    author = "匿名用户"
    author_el = soup.find("a", class_=re.compile("AuthorInfo-name|Author-name"))
    if not author_el:
        author_el = soup.find("span", class_=re.compile("AuthorInfo-name|Author-name"))
    if author_el:
        author = author_el.get_text(strip=True)

    pub_time = datetime.now()
    time_el = soup.find("div", re.compile("ContentItem-time|Answer-meta"))
    if time_el:
        time_text = time_el.get_text(strip=True)
        pub_time = parse_publish_time(time_text)

    content = soup.find("div", class_=re.compile("RichContent-inner|AnswerRichText"))
    if not content:
        content = soup.find("div", class_=re.compile("Post-RichText"))
    if not content:
        content = soup.find("div", class_="RichText")

    if not content:
        raise Exception("未找到正文内容，请检查Cookie是否有效")

    return {
        "title": title,
        "author": author,
        "published_at": pub_time,
        "content_element": content,
        "raw_html": str(content)
    }


def render_to_html(title, author, published_at, md_content, source_url):
    import markdown
    from services.note_importer import MARKDOWN_EXTENSIONS

    html_body = markdown.markdown(md_content, extensions=MARKDOWN_EXTENSIONS)
    date_str = published_at.strftime("%Y年%m月%d日")

    full_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            max-width: 800px;
            margin: 0 auto;
            padding: 40px 20px;
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Helvetica Neue", "Microsoft YaHei", sans-serif;
            line-height: 1.8;
            color: #333;
            background-color: #f4f5f6;
        }}
        .note-container {{
            background: white;
            padding: 40px;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.05);
        }}
        h1 {{
            font-size: 24px;
            font-weight: 700;
            line-height: 1.4;
            margin-bottom: 12px;
            color: #222;
        }}
        .meta-info {{
            font-size: 14px;
            color: #888;
            margin-bottom: 32px;
            display: flex;
            align-items: center;
            padding-bottom: 20px;
            border-bottom: 1px solid #eee;
            flex-wrap: wrap;
        }}
        .meta-info .author {{
            color: #0084ff;
            font-weight: 500;
            margin-right: 16px;
        }}
        .meta-info .date {{
            color: #b2b2b2;
            margin-right: 16px;
        }}
        .meta-info .source {{
            color: #8590a6;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 16px;
            color: #222;
            padding-bottom: 8px;
            border-bottom: 2px solid #0084ff;
        }}
        h3 {{
            font-size: 18px;
            font-weight: 600;
            margin-top: 24px;
            margin-bottom: 12px;
            color: #333;
        }}
        p {{
            margin-bottom: 16px;
            text-align: justify;
        }}
        code {{
            background: #f6f8fa;
            padding: 2px 8px;
            border-radius: 4px;
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-size: 14px;
            color: #e36209;
        }}
        pre {{
            background: #f6f8fa;
            padding: 16px;
            border-radius: 6px;
            overflow-x: auto;
            margin-bottom: 16px;
        }}
        pre code {{
            background: transparent;
            padding: 0;
            color: #24292e;
        }}
        img {{
            max-width: 100%;
            height: auto;
            border-radius: 8px;
            margin: 16px 0;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        }}
        blockquote {{
            border-left: 4px solid #0084ff;
            padding-left: 16px;
            color: #666;
            margin: 16px 0;
            background: #f8f9fa;
            padding: 12px 16px;
            border-radius: 0 8px 8px 0;
        }}
        a {{
            color: #0084ff;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
        ul, ol {{
            margin-bottom: 16px;
            padding-left: 24px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin-bottom: 16px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background: #f6f8fa;
            font-weight: 600;
        }}
    </style>
</head>
<body>
    <div class="note-container">
        <h1>{title}</h1>
        <div class="meta-info">
            <span class="author">👤 {author}</span>
            <span class="date">📅 {date_str}</span>
            <span class="source">📍 知乎专栏</span>
        </div>
        <div class="content">
{html_body}
        </div>
    </div>
</body>
</html>"""
    return full_html


def save_zhihu_article(url, cookie_str):
    html, session = fetch_zhihu_article(url, cookie_str)
    data = parse_zhihu_html(html)

    title = data["title"]
    author = data["author"]
    published_at = data["published_at"]

    converter = ZhihuConverter()
    md_content = converter.convert(str(data["content_element"]))

    article_id = generate_article_id(title, md_content)
    save_dir = BASE_DIR / "data" / "papers" / "zhihu"
    save_dir.mkdir(parents=True, exist_ok=True)

    html_path = save_dir / f"{article_id}.html"
    md_path = save_dir / f"{article_id}.md"

    html_content = render_to_html(title, author, published_at, md_content, url)

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(f"# {title}\n\n")
        f.write(f"> 作者：{author}\n")
        f.write(f"> 发布时间：{published_at.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"> 原文链接：{url}\n\n")
        f.write(md_content)

    abstract = md_content[:300].strip()
    if len(md_content) > 300:
        abstract += "..."

    return {
        "title": title,
        "author": author,
        "abstract": abstract,
        "content": md_content[:50000],
        "published_at": published_at.date(),
        "source_url": url,
        "file_path": f"data/papers/zhihu/{article_id}.html",
        "article_id": article_id
    }
