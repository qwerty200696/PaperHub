"""
arXiv Fetcher - arXiv 论文抓取服务
支持关键词搜索、分类筛选、时间范围过滤
"""
import re
import arxiv
import requests
from pathlib import Path
from datetime import datetime, timedelta

try:
    from backend.config import PAPERS_DIR, BASE_DIR
except ImportError:
    from config import PAPERS_DIR, BASE_DIR


def parse_arxiv_input(input_str):
    patterns = [
        r'arxiv\.org/(?:abs|pdf)/([\d.]+)',
        r'arXiv:([\d.]+)',
        r'^([\d.]+)$'
    ]

    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)

    raise ValueError(f"无法解析 arXiv 输入: {input_str}")


def fetch_arxiv_paper(arxiv_id):
    client = arxiv.Client()
    search = arxiv.Search(id_list=[arxiv_id])
    results = client.results(search)
    paper = next(results)

    return {
        'title': paper.title,
        'authors': [a.name for a in paper.authors],
        'abstract': paper.summary,
        'published_at': paper.published.date(),
        'pdf_url': paper.pdf_url,
        'categories': paper.categories,
        'doi': paper.doi,
        'arxiv_id': arxiv_id
    }


def download_pdf(pdf_url, arxiv_id):
    save_dir = PAPERS_DIR / 'arxiv'
    save_dir.mkdir(parents=True, exist_ok=True)

    file_path = save_dir / f"{arxiv_id}.pdf"

    if file_path.exists():
        return str(file_path.relative_to(BASE_DIR))

    response = requests.get(pdf_url, stream=True)
    response.raise_for_status()

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(file_path.relative_to(BASE_DIR))


def extract_pdf_text(file_path):
    try:
        import fitz
    except ImportError:
        return None

    try:
        full_path = file_path
        if not Path(full_path).is_absolute():
            full_path = BASE_DIR / file_path

        doc = fitz.open(str(full_path))
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        return '\n'.join(full_text)
    except Exception:
        return None


def download_generic_pdf(pdf_url, paper_id):
    """
    通用 PDF 下载函数，用于非 arXiv 来源的论文
    
    Args:
        pdf_url: PDF 文件的 URL
        paper_id: 论文 ID（用于生成文件名）
    
    Returns:
        保存的文件相对路径
    """
    save_dir = PAPERS_DIR / 'generic'
    save_dir.mkdir(parents=True, exist_ok=True)

    # 从 URL 提取文件扩展名，默认使用 .pdf
    url_path = pdf_url.split('?')[0]
    ext = Path(url_path).suffix or '.pdf'
    
    # 使用 paper_id 作为文件名，避免重复
    file_path = save_dir / f"{paper_id}{ext}"

    if file_path.exists():
        return str(file_path.relative_to(BASE_DIR))

    response = requests.get(pdf_url, stream=True)
    response.raise_for_status()

    with open(file_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)

    return str(file_path.relative_to(BASE_DIR))


def search_arxiv_papers(keywords=None, categories=None, max_results=20, 
                        start_date=None, end_date=None, sort_by='submittedDate',
                        sort_order='descending'):
    """
    搜索 arXiv 论文
    
    Args:
        keywords: 关键词列表，支持多关键词（AND逻辑），如 ['machine learning', 'deep learning']
        categories: arXiv 分类列表，如 ['cs.AI', 'stat.ML']
        max_results: 最大返回数量，默认20
        start_date: 开始日期（datetime对象），仅返回该日期之后发表的论文
        end_date: 结束日期（datetime对象），仅返回该日期之前发表的论文
        sort_by: 排序方式，可选 'submittedDate', 'updatedDate', 'relevance'
        sort_order: 排序顺序，可选 'ascending', 'descending'
    
    Returns:
        论文列表，每个元素是包含论文信息的字典
    """
    import logging
    logger = logging.getLogger('arxiv')
    
    client = arxiv.Client()
    
    # 构建查询字符串
    query_parts = []
    
    if keywords:
        if isinstance(keywords, str):
            keywords = [keywords]
        # 多关键词使用 AND 逻辑连接（不使用引号，避免触发限流）
        keyword_query = ' AND '.join(keywords)
        query_parts.append(keyword_query)
    
    if categories:
        if isinstance(categories, str):
            categories = [categories]
        # 多分类使用 OR 逻辑连接
        category_query = ' OR '.join(categories)
        query_parts.append(f'({category_query})')
    
    query = ' AND '.join(query_parts) if query_parts else 'cat:cs.*'
    
    logger.info(f"构建的查询字符串: {query}")
    logger.info(f"关键词: {keywords}, 分类: {categories}, 最大结果数: {max_results}")
    
    # 设置排序方式
    sort_by_map = {
        'submittedDate': arxiv.SortCriterion.SubmittedDate,
        'updatedDate': arxiv.SortCriterion.LastUpdatedDate,
        'relevance': arxiv.SortCriterion.Relevance
    }
    
    sort_order_map = {
        'ascending': arxiv.SortOrder.Ascending,
        'descending': arxiv.SortOrder.Descending
    }
    
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=sort_by_map.get(sort_by, arxiv.SortCriterion.SubmittedDate),
        sort_order=sort_order_map.get(sort_order, arxiv.SortOrder.Descending)
    )
    
    results = []
    try:
        for paper in client.results(search):
            # 时间范围过滤
            if start_date and paper.published.date() < start_date:
                continue
            if end_date and paper.published.date() > end_date:
                continue
            
            # 提取分类信息
            category_l1 = None
            category_l2 = None
            if paper.categories:
                primary_category = paper.categories[0]
                if '.' in primary_category:
                    category_l1, category_l2 = primary_category.split('.', 1)
                else:
                    category_l1 = primary_category
            
            results.append({
                'title': paper.title,
                'authors': [a.name for a in paper.authors],
                'abstract': paper.summary,
                'published_at': paper.published.date(),
                'pdf_url': paper.pdf_url,
                'categories': paper.categories,
                'category_l1': category_l1,
                'category_l2': category_l2,
                'doi': paper.doi,
                'arxiv_id': paper.get_short_id().replace('arXiv:', '') if paper.get_short_id() else None,
                'url': f"https://arxiv.org/abs/{paper.get_short_id().replace('arXiv:', '')}" if paper.get_short_id() else None
            })
        logger.info(f"搜索完成，共找到 {len(results)} 篇论文")
    except Exception as e:
        logger.error(f"搜索失败: {str(e)}")
        logger.error(f"错误类型: {type(e).__name__}")
        import traceback
        logger.error(f"堆栈跟踪: {traceback.format_exc()}")
        raise
    
    return results


def get_arxiv_categories():
    """
    获取 arXiv 分类列表
    
    Returns:
        分类字典，key为分类代码，value为分类名称
    """
    categories = {
        'cs.AI': 'Artificial Intelligence',
        'cs.AR': 'Hardware Architecture',
        'cs.CC': 'Computational Complexity',
        'cs.CE': 'Computational Engineering, Finance, and Science',
        'cs.CG': 'Computational Geometry',
        'cs.CL': 'Computation and Language',
        'cs.CR': 'Cryptography and Security',
        'cs.CV': 'Computer Vision and Pattern Recognition',
        'cs.CY': 'Computers and Society',
        'cs.DB': 'Databases',
        'cs.DC': 'Distributed, Parallel, and Cluster Computing',
        'cs.DL': 'Digital Libraries',
        'cs.DM': 'Discrete Mathematics',
        'cs.DS': 'Data Structures and Algorithms',
        'cs.ET': 'Emerging Technologies',
        'cs.FL': 'Formal Languages and Automata Theory',
        'cs.GL': 'General Literature',
        'cs.GR': 'Graphics',
        'cs.GT': 'Computer Science and Game Theory',
        'cs.HC': 'Human-Computer Interaction',
        'cs.IR': 'Information Retrieval',
        'cs.IT': 'Information Theory',
        'cs.LG': 'Machine Learning',
        'cs.LO': 'Logic in Computer Science',
        'cs.MA': 'Multiagent Systems',
        'cs.MM': 'Multimedia',
        'cs.MS': 'Mathematical Software',
        'cs.NA': 'Numerical Analysis',
        'cs.NE': 'Neural and Evolutionary Computing',
        'cs.NI': 'Networking',
        'cs.OH': 'Other Computer Science',
        'cs.OS': 'Operating Systems',
        'cs.PF': 'Performance',
        'cs.PL': 'Programming Languages',
        'cs.RO': 'Robotics',
        'cs.SC': 'Symbolic Computation',
        'cs.SD': 'Sound',
        'cs.SE': 'Software Engineering',
        'cs.SI': 'Social and Information Networks',
        'cs.SY': 'Systems and Control',
        'stat.ML': 'Machine Learning',
        'stat.AP': 'Statistics Applications',
        'stat.CO': 'Computational Statistics',
        'stat.ME': 'Methodology',
        'stat.TH': 'Statistics Theory',
        'physics.AI': 'Artificial Intelligence',
        'math.AP': 'Analysis of PDEs',
        'math.CA': 'Classical Analysis and ODEs',
        'math.CO': 'Combinatorics',
        'math.AG': 'Algebraic Geometry',
        'math.AT': 'Algebraic Topology',
        'math.CT': 'Category Theory',
        'math.CV': 'Complex Variables',
        'math.DG': 'Differential Geometry',
        'math.FA': 'Functional Analysis',
        'math.GM': 'General Mathematics',
        'math.GN': 'General Topology',
        'math.HO': 'History and Overview',
        'math.KT': 'K-Theory and Homology',
        'math.LO': 'Logic',
        'math.MG': 'Metric Geometry',
        'math.NT': 'Number Theory',
        'math.OA': 'Operator Algebras',
        'math.PR': 'Probability',
        'math.QA': 'Quantum Algebra',
        'math.RA': 'Rings and Algebras',
        'math.RT': 'Representation Theory',
        'math.SG': 'Symplectic Geometry',
        'math.SP': 'Spectral Theory',
        'math.ST': 'Statistics Theory'
    }
    return categories


def search_arxiv_by_keyword(keyword, max_results=10):
    """
    简单的关键词搜索接口（兼容旧接口）
    
    Args:
        keyword: 搜索关键词
        max_results: 最大返回数量
    
    Returns:
        论文列表
    """
    return search_arxiv_papers(keywords=[keyword], max_results=max_results)
