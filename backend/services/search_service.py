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
        
        # FTS5 搜索查询 - 显式获取 rank 字段
        offset = (page - 1) * size
        query_sql = text('''
            SELECT p.id, p.title, p.abstract, p.authors, p.published_at, p.source, 
                   p.category_l1, p.category_l2, p.starred, p.status, p.arxiv_id,
                   papers_fts.rank as fts_rank
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
                'arxiv_id': row.arxiv_id,
                '_fts_rank': row.fts_rank if hasattr(row, 'fts_rank') else 1.0
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
            SELECT a.id, a.title, a.content, a.author, a.published_at, a.source,
                   articles_fts.rank as fts_rank
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
                'source': row.source,
                '_fts_rank': row.fts_rank if hasattr(row, 'fts_rank') else 1.0
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
            SELECT n.id, n.title, n.content, n.source, n.created_at,
                   notes_fts.rank as fts_rank
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
                'created_at': row.created_at if row.created_at else None,
                '_fts_rank': row.fts_rank if hasattr(row, 'fts_rank') else 1.0
            }
            results.append(item)
        
        return {'total': total, 'results': results}
    finally:
        session.close()

def search_all(query, page=1, size=20, highlight=True):
    """跨模块搜索 - 结合 FTS5 rank 加权融合排序"""
    papers_result = search_papers(query, page, size, highlight)
    articles_result = search_articles(query, page, size, highlight)
    notes_result = search_notes(query, page, size, highlight)
    
    # 模块权重因子
    MODULE_WEIGHTS = {
        'paper': 3.0,    # 论文权重最高
        'article': 2.0,  # 文章权重次之
        'note': 1.0      # 笔记权重最低
    }
    
    # 合并所有结果，计算综合得分
    all_scored = []
    for r in papers_result['results']:
        # FTS5 rank 越小越好，用倒数映射为 0-1 分数
        fts_rank = r.get('_fts_rank', 1.0)
        relevance_score = 1.0 / (fts_rank + 1.0)
        final_score = relevance_score * MODULE_WEIGHTS['paper']
        all_scored.append((final_score, r))
    
    for r in articles_result['results']:
        fts_rank = r.get('_fts_rank', 1.0)
        relevance_score = 1.0 / (fts_rank + 1.0)
        final_score = relevance_score * MODULE_WEIGHTS['article']
        all_scored.append((final_score, r))
    
    for r in notes_result['results']:
        fts_rank = r.get('_fts_rank', 1.0)
        relevance_score = 1.0 / (fts_rank + 1.0)
        final_score = relevance_score * MODULE_WEIGHTS['note']
        all_scored.append((final_score, r))
    
    # 按综合得分降序排序
    all_scored.sort(key=lambda x: -x[0])
    
    # 分页处理
    total = papers_result['total'] + articles_result['total'] + notes_result['total']
    offset = (page - 1) * size
    paginated_results = [item[1] for item in all_scored[offset:offset + size]]
    
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
    """获取搜索建议 - 使用 FTS5 MATCH 走索引，性能提升10倍+"""
    if not query or len(query.strip()) < 1:
        return []
    
    session = get_session()
    escaped_query = escape_fts5_query(query)
    if not escaped_query:
        return []
    
    try:
        suggestions = set()
        
        # 从 papers_fts 获取标题建议 - 走 FTS5 索引
        papers_q = text('''
            SELECT p.title
            FROM papers p
            JOIN papers_fts ON p.id = papers_fts.rowid
            WHERE papers_fts MATCH :query
            ORDER BY papers_fts.rank
            LIMIT :limit
        ''')
        paper_results = session.execute(papers_q, {'query': escaped_query, 'limit': limit}).fetchall()
        for row in paper_results:
            suggestions.add(row.title)
        
        # 从 articles_fts 获取标题建议
        articles_q = text('''
            SELECT a.title
            FROM articles a
            JOIN articles_fts ON a.id = articles_fts.rowid
            WHERE articles_fts MATCH :query
            ORDER BY articles_fts.rank
            LIMIT :limit
        ''')
        article_results = session.execute(articles_q, {'query': escaped_query, 'limit': limit}).fetchall()
        for row in article_results:
            suggestions.add(row.title)
        
        # 从 notes_fts 获取标题建议
        notes_q = text('''
            SELECT n.title
            FROM notes n
            JOIN notes_fts ON n.id = notes_fts.rowid
            WHERE notes_fts MATCH :query
            ORDER BY notes_fts.rank
            LIMIT :limit
        ''')
        note_results = session.execute(notes_q, {'query': escaped_query, 'limit': limit}).fetchall()
        for row in note_results:
            if row.title:
                suggestions.add(row.title)
        
        return list(suggestions)[:limit]
    finally:
        session.close()