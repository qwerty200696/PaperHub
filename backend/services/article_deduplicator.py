"""
Article Deduplicator - 文章去重机制
"""
import re


def normalize_title(title):
    """标准化标题用于比较 - 支持中英文"""
    if not title:
        return ''
    title = title.lower().strip()
    # 保留系列文章标识（上、下、第一部分、第二部分等）
    # 这些是区分不同文章的重要标识，不能移除
    title = re.sub(r'[^\w\s\u4e00-\u9fff（）()上中下第部篇章节卷]', '', title, flags=re.UNICODE)
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


def has_series_identifier(title):
    """检测标题是否包含系列文章标识"""
    series_patterns = [
        r'（[上下]）$',           # （上）、（下）结尾
        r'\([上下]\)$',           # (上)、(下)结尾
        r'（[一二三四五六七八九十]）$',  # （一）、（二）等结尾
        r'\([一二三四五六七八九十]\)$',  # (一)、(二)等结尾
        r'（第[一二三四五六七八九十]部分）$',  # （第一部分）等结尾
        r'（第[一二三四五六七八九十]章）$',    # （第一章）等结尾
        r'（第[一二三四五六七八九十]节）$',    # （第一节）等结尾
        r'-第[一二三四五六七八九十][章节篇卷部]',  # -第一章 等
        r'_[一二三四五六七八九十]$',  # _1、_2 结尾
        r' [一二三四五六七八九十]$',   # 空格加数字结尾
        r'_[0-9]+$',              # _1、_2 数字结尾
        r' [0-9]+$',              # 空格加数字结尾
        r'-[0-9]+$',              # -1、-2 结尾
        r'_[0-9]+$',              # _1、_2 结尾
    ]
    for pattern in series_patterns:
        if re.search(pattern, title):
            return True
    return False


def get_series_identifier(title):
    """提取标题中的系列标识"""
    series_patterns = [
        r'（([上下])）$',
        r'\(([上下])\)$',
        r'（([一二三四五六七八九十])）$',  # 新增：（一）、（二）格式
        r'\(([一二三四五六七八九十])\)$',  # 新增：(一)、(二)格式
        r'（第([一二三四五六七八九十])部分）$',
        r'（第([一二三四五六七八九十])章）$',
        r'（第([一二三四五六七八九十])节）$',
        r'-第([一二三四五六七八九十])[章节篇卷部]',
    ]
    for pattern in series_patterns:
        match = re.search(pattern, title)
        if match:
            return match.group(1)
    return None


def title_similarity(title1, title2, threshold=0.85):
    """计算两个标题的相似度 - 支持中英文

    使用字符级比较 + 编辑距离，对中文无空格标题更有效
    
    特殊处理：如果两个标题都包含系列文章标识但标识不同，则认为不是重复
    """
    # 检测系列文章标识
    has_series1 = has_series_identifier(title1)
    has_series2 = has_series_identifier(title2)
    
    # 如果两个标题都有系列标识且标识不同，则认为不是重复（返回低相似度）
    if has_series1 and has_series2:
        series1 = get_series_identifier(title1)
        series2 = get_series_identifier(title2)
        if series1 and series2 and series1 != series2:
            # 系列标识不同，降低相似度
            return 0.7  # 低于默认阈值0.85，不会被认为重复
    
    norm1 = normalize_title(title1)
    norm2 = normalize_title(title2)

    if norm1 == norm2:
        return 1.0

    if not norm1 or not norm2:
        return 0.0

    set1 = set(norm1)
    set2 = set(norm2)

    intersection = len(set1 & set2)
    union = len(set1 | set2)
    char_jaccard = intersection / union if union > 0 else 0.0

    max_len = max(len(norm1), len(norm2))
    distance = levenshtein_distance(norm1, norm2)
    edit_sim = 1.0 - (distance / max_len)

    return max(char_jaccard, edit_sim)


def content_hash(content, length=500):
    """计算内容哈希值"""
    if not content:
        return ''
    content_sample = content[:length].strip().lower()
    content_sample = re.sub(r'\s+', '', content_sample)
    return content_sample


def check_article_duplicate(session, Article, title=None, content=None, url=None, threshold=0.8):
    """检查文章是否已存在

    去重策略：
    1. URL 完全匹配（最高优先级）
    2. 标题相似度 >= threshold
    3. 内容前500字符相同

    Returns:
        None if not duplicate
        Article object if duplicate
    """
    if url and url.strip():
        existing = session.query(Article).filter(
            Article.is_deleted == False,
            Article.url == url.strip()
        ).first()
        if existing:
            return existing

    if title:
        all_articles = session.query(Article).filter(Article.is_deleted == False).all()
        for article in all_articles:
            if article.title:
                sim = title_similarity(title, article.title, threshold)
                if sim >= threshold:
                    return article

    if content:
        hash1 = content_hash(content)
        if hash1:
            all_articles = session.query(Article).filter(Article.is_deleted == False).all()
            for article in all_articles:
                if article.content:
                    hash2 = content_hash(article.content)
                    if hash1 == hash2:
                        return article

    return None
