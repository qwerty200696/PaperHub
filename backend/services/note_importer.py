import re
import hashlib
from datetime import datetime
from pathlib import Path
import markdown

MARKDOWN_EXTENSIONS = [
    'extra',
    'codehilite',
    'toc',
    'tables',
    'fenced_code',
    'nl2br',
    'sane_lists'
]

def render_markdown_to_html(md_content: str, title: str, source: str, created_at: datetime = None) -> str:
    """将Markdown内容渲染为完整的HTML页面"""
    if created_at is None:
        created_at = datetime.now()
    
    html_body = markdown.markdown(md_content, extensions=MARKDOWN_EXTENSIONS)
    date_str = created_at.strftime('%Y年%m月%d日 %H:%M')
    
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
        }}
        .meta-info .source {{
            color: #576b95;
            font-weight: 500;
            margin-right: 16px;
        }}
        .meta-info .date {{
            color: #b2b2b2;
        }}
        h2 {{
            font-size: 20px;
            font-weight: 600;
            margin-top: 32px;
            margin-bottom: 16px;
            color: #222;
            padding-bottom: 8px;
            border-bottom: 2px solid #576b95;
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
            border-radius: 8px;
            overflow-x: auto;
            margin: 16px 0;
        }}
        pre code {{
            background: none;
            padding: 0;
            color: #24292e;
        }}
        blockquote {{
            border-left: 4px solid #576b95;
            padding-left: 16px;
            margin: 16px 0;
            color: #6a737d;
            background: #f8f9fa;
            padding-top: 8px;
            padding-bottom: 8px;
            border-radius: 0 8px 8px 0;
        }}
        ul, ol {{
            padding-left: 24px;
            margin-bottom: 16px;
        }}
        li {{
            margin-bottom: 8px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 16px 0;
        }}
        th, td {{
            border: 1px solid #e1e4e8;
            padding: 8px 12px;
            text-align: left;
        }}
        th {{
            background: #f6f8fa;
            font-weight: 600;
        }}
        hr {{
            border: none;
            border-top: 1px solid #e1e4e8;
            margin: 32px 0;
        }}
        strong {{
            color: #222;
            font-weight: 600;
        }}
        a {{
            color: #0366d6;
            text-decoration: none;
        }}
        a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="note-container">
        <h1>{title}</h1>
        <div class="meta-info">
            <span class="source">{source}</span>
            <span class="date">{date_str}</span>
        </div>
        <div class="content">
{html_body}
        </div>
    </div>
</body>
</html>
"""
    return full_html


def generate_note_id(title: str, content: str) -> str:
    """根据标题和内容哈希生成唯一的笔记ID"""
    content_hash = hashlib.md5(f"{title}:{content[:500]}".encode()).hexdigest()[:8]
    return f"note_{content_hash}"


def save_note(title: str, source: str, md_content: str, created_at: datetime = None, subfolder: str = 'notes') -> dict:
    """
    保存笔记，同时存为.md和.html两个文件
    
    Args:
        subfolder: 子文件夹名称，如 'notes' 或 'zhihu'
    
    Returns:
        dict: 包含文件路径等信息的字典
    """
    from config import BASE_DIR
    
    if created_at is None:
        created_at = datetime.now()
    
    note_id = generate_note_id(title, md_content)
    save_dir = BASE_DIR / 'data' / 'papers' / subfolder
    save_dir.mkdir(parents=True, exist_ok=True)
    
    html_path = save_dir / f'{note_id}.html'
    md_path = save_dir / f'{note_id}.md'
    
    html_content = render_markdown_to_html(md_content, title, source, created_at)
    
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    with open(md_path, 'w', encoding='utf-8') as f:
        f.write(f"# {title}\n\n")
        f.write(f"> 来源: {source}\n")
        f.write(f"> 创建时间: {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write(md_content)
    
    abstract = md_content[:200].strip()
    if len(md_content) > 200:
        abstract += '...'
    
    return {
        'title': title,
        'author': '',
        'account_name': source,
        'abstract': abstract,
        'content': md_content[:50000],
        'html_content': md_content,
        'published_at': created_at.date(),
        'source_url': f'note://{note_id}',
        'file_path': f'data/papers/notes/{note_id}.html',
        'note_id': note_id
    }
