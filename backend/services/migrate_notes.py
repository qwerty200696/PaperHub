"""
对话笔记迁移工具
将 source='note' 的 Paper 迁移到新的 Note 系统
"""
import json


def migrate_dialogue_notes():
    """
    一键迁移：把所有 source='note' 的 Paper 转为 Note
    对话笔记 → 建立自我关联
    迁移后 Paper source 改为 'note_migrated'
    """
    try:
        from backend.config import get_session
        from backend.models import Paper, Note
    except ImportError:
        from config import get_session
        from models import Paper, Note

    session = get_session()
    migrated_count = 0

    try:
        papers = session.query(Paper).filter(Paper.source == 'note').all()

        for paper in papers:
            existing = session.query(Note).filter(
                Note.content == paper.content,
                Note.source == paper.extra
            ).first()

            if existing:
                paper.source = 'note_migrated'
                if paper not in existing.papers:
                    existing.papers.append(paper)
                migrated_count += 1
                continue

            source = 'manual'
            if paper.extra:
                try:
                    extra = json.loads(paper.extra) if isinstance(paper.extra, str) else paper.extra
                    source = extra.get('llm_source', 'manual')
                except (json.JSONDecodeError, TypeError):
                    source = 'manual'

            note = Note(
                title=paper.title or '',
                content=paper.content,
                source=source
            )
            session.add(note)
            session.flush()

            note.papers.append(paper)
            paper.source = 'note_migrated'
            migrated_count += 1

        session.commit()
        return migrated_count

    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
