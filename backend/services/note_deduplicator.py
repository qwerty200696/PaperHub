"""
Note Deduplicator - 笔记去重机制
"""
import re
from sqlalchemy import or_


def normalize_title(title):
    """标准化标题用于比较 - 支持中英文"""
    if not title:
        return ''
    title = title.lower().strip()
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


def content_hash(content, length=500):
    """计算内容哈希值（用于检测重复）"""
    if not content:
        return ''
    content_sample = content[:length].strip().lower()
    content_sample = re.sub(r'\s+', '', content_sample)
    return content_sample


def check_note_duplicate(session, Note, title=None, content=None, url=None, threshold=0.8):
    """检查笔记是否已存在
    
    去重策略：
    1. URL 完全匹配（最高优先级）
    2. 标题相似度 >= threshold
    3. 内容前500字符相同
    
    Returns:
        None if not duplicate
        Note object if duplicate
    """
    # 1. URL 完全匹配
    if url and url.strip():
        existing = session.query(Note).filter(
            Note.is_deleted == False,
            Note.url == url.strip()
        ).first()
        if existing:
            return existing
    
    # 2. 标题相似度匹配
    if title:
        all_notes = session.query(Note).filter(Note.is_deleted == False).all()
        for note in all_notes:
            if note.title:
                sim = title_similarity(title, note.title, threshold)
                if sim >= threshold:
                    return note
    
    # 3. 内容匹配（前500字符）
    if content:
        hash1 = content_hash(content)
        if hash1:
            all_notes = session.query(Note).filter(Note.is_deleted == False).all()
            for note in all_notes:
                if note.content:
                    hash2 = content_hash(note.content)
                    if hash1 == hash2:
                        return note
    
    return None


def find_all_duplicates(session, Note, threshold=0.85):
    """查找所有重复笔记组"""
    all_notes = session.query(Note).filter(Note.is_deleted == False).all()
    duplicates = []
    checked = set()
    
    for i, note1 in enumerate(all_notes):
        if note1.id in checked:
            continue
        
        group = [note1]
        
        for j, note2 in enumerate(all_notes):
            if i >= j:
                continue
            if note2.id in checked:
                continue
            
            is_duplicate = False
            
            # URL 匹配
            if note1.url and note2.url and note1.url == note2.url:
                is_duplicate = True
            
            # 标题相似度匹配
            elif note1.title and note2.title:
                sim = title_similarity(note1.title, note2.title, threshold)
                if sim >= threshold:
                    is_duplicate = True
            
            # 内容匹配
            elif note1.content and note2.content:
                hash1 = content_hash(note1.content)
                hash2 = content_hash(note2.content)
                if hash1 and hash2 and hash1 == hash2:
                    is_duplicate = True
            
            if is_duplicate:
                group.append(note2)
                checked.add(note2.id)
        
        if len(group) > 1:
            duplicates.append(group)
            checked.add(note1.id)
    
    return duplicates


def remove_duplicates(session, Note, keep_oldest=True, dry_run=False):
    """移除重复笔记
    
    Args:
        session: 数据库会话
        Note: Note 模型类
        keep_oldest: True=保留最早创建的, False=保留最新的
        dry_run: True=只模拟不执行
    
    Returns:
        {
            'total_groups': int,
            'total_removed': int,
            'details': list of removed note info
        }
    """
    duplicates = find_all_duplicates(session, Note)
    removed = []
    
    for group in duplicates:
        if keep_oldest:
            # 保留最早创建的
            group.sort(key=lambda n: n.created_at)
            to_remove = group[1:]
            keep_note = group[0]
        else:
            # 保留最新的
            group.sort(key=lambda n: n.created_at, reverse=True)
            to_remove = group[1:]
            keep_note = group[0]
        
        for note in to_remove:
            if not dry_run:
                note.is_deleted = True
            removed.append({
                'removed_id': note.id,
                'removed_title': note.title,
                'removed_created_at': note.created_at.isoformat() if note.created_at else None,
                'kept_id': keep_note.id,
                'kept_title': keep_note.title
            })
    
    if not dry_run:
        session.commit()
    
    return {
        'total_groups': len(duplicates),
        'total_removed': len(removed),
        'details': removed
    }
