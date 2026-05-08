"""
Deduplicator - 论文去重机制
"""
import re
import hashlib


def normalize_title(title):
    """标准化标题用于比较 - 支持中英文"""
    if not title:
        return ''
    title = title.lower()
    title = re.sub(r'[^\w\s\u4e00-\u9fff]', '', title, flags=re.UNICODE)
    title = re.sub(r'\s+', ' ', title)
    return title.strip()


def levenshtein_distance(s1, s2):
    """计算编辑距离"""
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def title_similarity(title1, title2, threshold=0.85):
    """计算两个标题的相似度 - 支持中英文
    
    使用词级比较 + 编辑距离，提高准确性
    """
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)
    
    if norm1 == norm2:
        return 1.0
    
    if not norm1 or not norm2:
        return 0.0
    
    # 词级别 Jaccard 相似度（更好地区分不同标题）
    words1 = set(norm1.split())
    words2 = set(norm2.split())
    
    if words1 and words2:
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        word_jaccard = intersection / union if union > 0 else 0.0
    else:
        word_jaccard = 0.0
    
    # 字符级别比较作为补充
    set1 = set(norm1)
    set2 = set(norm2)
    intersection = len(set1 & set2)
    union = len(set1 | set2)
    char_jaccard = intersection / union if union > 0 else 0.0
    
    max_len = max(len(norm1), len(norm2))
    distance = levenshtein_distance(norm1, norm2)
    edit_sim = 1.0 - (distance / max_len)
    
    # 综合考虑：词级别相似度权重更高
    return (word_jaccard * 0.6 + char_jaccard * 0.2 + edit_sim * 0.2)


def check_duplicate(session, Paper, title=None, doi=None, arxiv_id=None, url=None):
    """检查论文是否已存在
    
    Returns:
        None if not duplicate
        Paper object if duplicate
    """
    if arxiv_id:
        existing = session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        if existing:
            return existing
    
    if doi:
        existing = session.query(Paper).filter(Paper.doi == doi).first()
        if existing:
            return existing
    
    if url:
        existing = session.query(Paper).filter(Paper.url == url).first()
        if existing:
            return existing
    
    if title:
        norm_title = normalize_title(title)
        if not norm_title:
            return None
        
        all_papers = session.query(Paper).all()
        for paper in all_papers:
            sim = title_similarity(title, paper.title)
            if sim >= 0.8:
                return paper
    
    return None


def get_duplicate_info(paper, duplicate_type):
    """获取重复信息"""
    return {
        'duplicate': True,
        'duplicate_type': duplicate_type,
        'paper_id': paper.id,
        'title': paper.title,
        'url': paper.url
    }
