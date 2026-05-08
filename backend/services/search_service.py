"""全文检索服务"""

import re
from sqlalchemy import text
from config import get_session
from models.paper import Paper, Article, Note

def escape_fts5_query(query):
    """转义 FTS5 查询中的特殊字符"""
    if not query:
        return query
    # FTS5 特殊字符处理：
    # - 冒号(:) 用于列限定符，需要转义或替换
    # - 双引号用于短语搜索
    # - 逗号(,) 用于分隔多个搜索项
    # - 其他特殊字符可能影响查询语法
    
    # 将特殊字符替换为空格，支持多词搜索
    # 这样 "TACO: CLI Agent" 变成 "TACO CLI Agent"
    special_pattern = r'[:,\\"\'(){}[\]^*+?!@#$%&|~]'
    query = re.sub(special_pattern, ' ', query)
    
    # 将多个连续空格合并为一个
    query = re.sub(r'\s+', ' ', query).strip()
    
    return query

def highlight_text(text, keywords):
    """高亮匹配的关键词"""
    if not text or not keywords:
        return text
    
    for keyword in keywords:
        if keyword.strip():
            pattern = re.escape(keyword.strip())
            text = re.sub(f'({pattern})', r'<em>\1</em>', text, flags=re.IGNORECASE)
    return text

def search_papers(query, page=1, size=20, highlight=True):
    """搜索论文"""
    session = get_session()
    try:
        escaped_query = escape_fts5_query(query)
        keywords = escaped_query.split() if escaped_query else []
        
        # FTS5 搜索查询
        offset = (page - 1) * size
        query_sql = text('''
            SELECT p.id, p.title, p.abstract, p.authors, p.published_at, p.source, 
                   p.category_l1, p.category_l2, p.starred, p.status, p.arxiv_id,
                   papers_fts.title AS fts_title, papers_fts.abstract AS fts_abstract
            FROM papers p
            JOIN papers_fts ON p.id = papers_fts.rowid
            WHERE papers_fts MATCH :query
            ORDER BY papers_fts.rank
            LIMIT :limit OFFSET :offset
        ''')
        
        result = session.execute(
            query_sql,
            {'query': escaped_query, 'limit': size, 'offset': offset}
        ).fetchall()
        
        # 统计总数
        count_sql = text('''
            SELECT COUNT(DISTINCT p.id)
            FROM papers p
            JOIN papers_fts ON p.id = papers_fts.rowid
            WHERE papers_fts MATCH :query
        ''')
        total = session.execute(count_sql, {'query': escaped_query}).scalar() or 0
        
        results = []
        for row in result:
            item = {
                'id': row.id,
                'type': 'paper',
                'title': row.title,
                'title_highlight': highlight_text(row.title, keywords) if highlight else row.title,
                'abstract': row.abstract[:500] + '...' if row.abstract and len(row.abstract) > 500 else row.abstract,
                'abstract_highlight': highlight_text(row.abstract[:500] + '...', keywords) if highlight and row.abstract else None,
                'authors': row.authors,
                'published_at': row.published_at if row.published_at else None,
                'source': row.source or 'arXiv',
                'category_l1': row.category_l1,
                'category_l2': row.category_l2,
                'starred': row.starred,
                'status': row.status,
                'arxiv_id': row.arxiv_id
            }
            results.append(item)
        
        return {'total': total, 'results': results}
    finally:
        session.close()

def search_articles(query, page=1, size=20, highlight=True):
    """搜索文章"""
    session = get_session()
    try:
        escaped_query = escape_fts5_query(query)
        keywords = escaped_query.split() if escaped_query else []
        
        offset = (page - 1) * size
        query_sql = text('''
            SELECT a.id, a.title, a.content, a.author, a.published_at, a.source
            FROM articles a
            JOIN articles_fts ON a.id = articles_fts.rowid
            WHERE articles_fts MATCH :query
            ORDER BY articles_fts.rank
            LIMIT :limit OFFSET :offset
        ''')
        
        result = session.execute(
            query_sql,
            {'query': escaped_query, 'limit': size, 'offset': offset}
        ).fetchall()
        
        count_sql = text('''
            SELECT COUNT(DISTINCT a.id)
            FROM articles a
            JOIN articles_fts ON a.id = articles_fts.rowid
            WHERE articles_fts MATCH :query
        ''')
        total = session.execute(count_sql, {'query': escaped_query}).scalar() or 0
        
        results = []
        for row in result:
            # 提取纯文本摘要（去掉HTML标签）
            content_text = re.sub(r'<[^>]+>', '', row.content) if row.content else ''
            summary = content_text[:300] + '...' if len(content_text) > 300 else content_text
            
            item = {
                'id': row.id,
                'type': 'article',
                'title': row.title,
                'title_highlight': highlight_text(row.title, keywords) if highlight else row.title,
                'summary': summary,
                'summary_highlight': highlight_text(summary, keywords) if highlight else summary,
                'author': row.author,
                'published_at': row.published_at if row.published_at else None,
                'source': row.source
            }
            results.append(item)
        
        return {'total': total, 'results': results}
    finally:
        session.close()

def search_notes(query, page=1, size=20, highlight=True):
    """搜索笔记"""
    session = get_session()
    try:
        escaped_query = escape_fts5_query(query)
        keywords = escaped_query.split() if escaped_query else []
        
        offset = (page - 1) * size
        query_sql = text('''
            SELECT n.id, n.title, n.content, n.source, n.created_at
            FROM notes n
            JOIN notes_fts ON n.id = notes_fts.rowid
            WHERE notes_fts MATCH :query
            ORDER BY notes_fts.rank
            LIMIT :limit OFFSET :offset
        ''')
        
        result = session.execute(
            query_sql,
            {'query': escaped_query, 'limit': size, 'offset': offset}
        ).fetchall()
        
        count_sql = text('''
            SELECT COUNT(DISTINCT n.id)
            FROM notes n
            JOIN notes_fts ON n.id = notes_fts.rowid
            WHERE notes_fts MATCH :query
        ''')
        total = session.execute(count_sql, {'query': escaped_query}).scalar() or 0
        
        results = []
        for row in result:
            # 提取纯文本摘要（去掉Markdown格式）
            content_text = re.sub(r'[#*`>\-\[\]]', '', row.content) if row.content else ''
            summary = content_text[:300] + '...' if len(content_text) > 300 else content_text
            
            item = {
                'id': row.id,
                'type': 'note',
                'title': row.title,
                'title_highlight': highlight_text(row.title, keywords) if highlight else row.title,
                'summary': summary,
                'summary_highlight': highlight_text(summary, keywords) if highlight else summary,
                'source': row.source,
                'created_at': row.created_at if row.created_at else None
            }
            results.append(item)
        
        return {'total': total, 'results': results}
    finally:
        session.close()

def search_all(query, page=1, size=20, highlight=True):
    """跨模块搜索"""
    papers_result = search_papers(query, page, size, highlight)
    articles_result = search_articles(query, page, size, highlight)
    notes_result = search_notes(query, page, size, highlight)
    
    # 合并结果并按相关性排序
    all_results = []
    all_results.extend([(r, 3) for r in papers_result['results']])  # 论文权重最高
    all_results.extend([(r, 2) for r in articles_result['results']])  # 文章权重次之
    all_results.extend([(r, 1) for r in notes_result['results']])  # 笔记权重最低
    
    # 排序：权重 + 相关性
    all_results.sort(key=lambda x: -x[1])
    
    # 分页处理
    total = papers_result['total'] + articles_result['total'] + notes_result['total']
    offset = (page - 1) * size
    paginated_results = [r[0] for r in all_results[offset:offset + size]]
    
    return {
        'total': total,
        'results': paginated_results,
        'breakdown': {
            'papers': papers_result['total'],
            'articles': articles_result['total'],
            'notes': notes_result['total']
        }
    }

def get_search_suggestions(query, limit=5):
    """获取搜索建议"""
    if not query:
        return []
    
    session = get_session()
    try:
        suggestions = set()
        
        # 从论文标题获取建议
        paper_query = text('''
            SELECT DISTINCT title FROM papers 
            WHERE title LIKE :prefix
            ORDER BY title LIMIT :limit
        ''')
        paper_results = session.execute(paper_query, {'prefix': f'%{query}%', 'limit': limit}).fetchall()
        for row in paper_results:
            suggestions.add(row.title)
        
        # 从文章标题获取建议
        article_query = text('''
            SELECT DISTINCT title FROM articles 
            WHERE title LIKE :prefix
            ORDER BY title LIMIT :limit
        ''')
        article_results = session.execute(article_query, {'prefix': f'%{query}%', 'limit': limit}).fetchall()
        for row in article_results:
            suggestions.add(row.title)
        
        # 从笔记标题获取建议
        note_query = text('''
            SELECT DISTINCT title FROM notes 
            WHERE title LIKE :prefix
            ORDER BY title LIMIT :limit
        ''')
        note_results = session.execute(note_query, {'prefix': f'%{query}%', 'limit': limit}).fetchall()
        for row in note_results:
            suggestions.add(row.title)
        
        return list(suggestions)[:limit]
    finally:
        session.close()