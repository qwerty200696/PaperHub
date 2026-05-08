"""
Database Models - 数据库模型
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

try:
    from backend.models.paper import (
        Paper, Tag, Note, Article, PaperVersion, WechatSubscription,
        paper_tags, note_tags, note_papers,
        article_papers, article_tags, note_articles
    )
except ImportError:
    from models.paper import (
        Paper, Tag, Note, Article, PaperVersion, WechatSubscription,
        paper_tags, note_tags, note_papers,
        article_papers, article_tags, note_articles
    )

__all__ = [
    'Base', 'Paper', 'Tag', 'Note', 'Article', 'PaperVersion', 'WechatSubscription', 'WechatConfig',
    'paper_tags', 'note_tags', 'note_papers',
    'article_papers', 'article_tags', 'note_articles'
]
