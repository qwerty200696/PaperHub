"""
PDF Processor - PDF文件处理和元数据提取
改进的元数据提取算法
"""
import re
from pathlib import Path
from PyPDF2 import PdfReader


def extract_pdf_text(file_path, max_pages=50):
    """提取PDF文本内容"""
    try:
        reader = PdfReader(file_path)
        text_parts = []
        pages_to_read = min(len(reader.pages), max_pages)
        
        for i in range(pages_to_read):
            text_parts.append(reader.pages[i].extract_text() or '')
        
        return '\n'.join(text_parts)
    except Exception as e:
        print(f"PDF text extraction error: {e}")
        return ''


def extract_title_from_filename(filename):
    """从文件名提取标题（去除版本号、日期等）"""
    if not filename:
        return None
    
    # 去除扩展名
    name = Path(filename).stem
    
    # 去除版本号（如 v1, v2, v1.0）
    name = re.sub(r'_v\d+(\.\d+)?$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'-v\d+(\.\d+)?$', '', name, flags=re.IGNORECASE)
    
    # 去除日期（如 20240101, 2024-01-01）
    name = re.sub(r'_\d{4}[-_]?\d{2}[-_]?\d{2}$', '', name)
    
    # 去除arxiv ID（如 2604.01707）
    name = re.sub(r'^\d{4}\.\d+[_-]', '', name)
    name = re.sub(r'[_-]\d{4}\.\d+$', '', name)
    
    # 下划线转空格
    name = name.replace('_', ' ').replace('-', ' ')
    
    # 多个空格合并
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 去除常见的前缀
    name = re.sub(r'^[Pp]aper[_-]', '', name)
    name = re.sub(r'^[Aa]rXiv[_-]', '', name)
    
    return name if len(name) > 5 else None


def extract_metadata_from_text(text):
    """从文本中提取元数据（标题、作者等）"""
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    title = None
    authors = []
    abstract = None
    
    # 1. 尝试从文本开头提取标题（通常在前几行）
    title_lines = []
    in_title_section = True
    for i, line in enumerate(lines[:15]):
        # 跳过明显不是标题的行
        if line.lower().startswith(('abstract', 'introduction', 'keywords', 'arxiv:', 'doi:', 'preprint', 'submitted')):
            break
        if line.lower().startswith(('author', 'authors')):
            break
        if '@' in line or 'arxiv.org' in line.lower():
            continue
        if len(line) < 3:
            continue
        
        # 检查是否看起来像作者行（包含数字上标如 1,2,* 等）
        if re.search(r'(\[\d+\]|\^\d+|\(\d+\)|1,2|2,3|\*)', line) and len(line) > 30:
            break
            
        title_lines.append(line)
        if len(title_lines) >= 3:
            break
    
    if title_lines:
        title = ' '.join(title_lines)
        title = re.sub(r'\s+', ' ', title).strip()
        # 去除结尾的标点
        title = re.sub(r'[.,;:]$', '', title)
        if len(title) > 200:
            title = title[:200] + '...'
    
    # 2. 提取作者（在标题之后，通常包含数字上标）
    author_section_start = len(title_lines) if title_lines else 0
    for i in range(author_section_start, min(author_section_start + 10, len(lines))):
        line = lines[i]
        # 作者行通常包含数字上标或邮箱
        if re.search(r'(\[\d+\]|\^\d+|\(\d+\)|1,2|2,3|\*)', line):
            # 提取作者名（去除数字上标）
            potential_authors = re.sub(r'(\[\d+\]|\^\d+|\(\d+\)|\*)', '', line)
            # 按分隔符分割
            for sep in [';', ',', 'and', 'et al']:
                if sep in potential_authors.lower():
                    authors.extend([a.strip() for a in re.split(r';|,|\band\b', potential_authors, flags=re.IGNORECASE) if a.strip()])
                    break
            if not authors:
                # 尝试按大写字母分割
                parts = re.findall(r'([A-Z][a-zA-Z-]+(?:\s+[A-Z][a-zA-Z-]+)*)', line)
                authors.extend([p.strip() for p in parts if len(p) > 2])
    
    # 清理作者列表
    authors = [a for a in authors if len(a) > 2 and '@' not in a and not a.isdigit()]
    authors = list(dict.fromkeys(authors))[:10]  # 去重，最多10个作者
    
    # 3. 提取摘要
    abstract_start = None
    for i, line in enumerate(lines[:80]):
        if 'abstract' in line.lower() and len(line) < 50:
            abstract_start = i + 1
            break
    
    if abstract_start:
        abstract_lines = []
        for i in range(abstract_start, min(abstract_start + 40, len(lines))):
            line = lines[i]
            # 遇到下一个章节标题停止
            if re.match(r'^(1\.\s*)?(introduction|related work|conclusion|references|experiments|method)', line.lower()):
                break
            if line.lower().startswith('keywords'):
                break
            abstract_lines.append(line)
        
        abstract = ' '.join(abstract_lines)
        abstract = re.sub(r'\s+', ' ', abstract).strip()
        if len(abstract) > 600:
            abstract = abstract[:600] + '...'
    
    return {
        'title': title or None,
        'authors': authors if authors else None,
        'abstract': abstract or None,
    }


def process_pdf_file(file_path, filename=None):
    """处理单个PDF文件"""
    if filename is None:
        filename = Path(file_path).stem
    
    text = extract_pdf_text(file_path)
    metadata = extract_metadata_from_text(text)
    
    # 如果从文本中没有提取到标题，尝试从文件名提取
    if not metadata['title']:
        filename_title = extract_title_from_filename(filename)
        if filename_title:
            metadata['title'] = filename_title
    
    return {
        'title': metadata['title'] or '未命名论文',
        'authors': metadata['authors'] or ['未知作者'],
        'abstract': metadata['abstract'] or '',
        'content': text,
        'filename': filename,
        'source': 'pdf_upload'
    }
