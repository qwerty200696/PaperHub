"""
Database Models - 数据库模型
"""
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

try:
    from backend.models.user import User
except ImportError:
    from models.user import User

try:
    from backend.models.mixins import UserOwnedMixin
except ImportError:
    from models.mixins import UserOwnedMixin

try:
    from backend.models.paper import (
        Paper, Tag, Note, Article, PaperVersion, WechatSubscription, WechatConfig,
        UserPaperStatus,
        paper_tags, note_tags, note_papers,
        article_papers, article_tags, note_articles
    )
except ImportError:
    from models.paper import (
        Paper, Tag, Note, Article, PaperVersion, WechatSubscription, WechatConfig,
        UserPaperStatus,
        paper_tags, note_tags, note_papers,
        article_papers, article_tags, note_articles
    )

__all__ = [
    'Base', 'User', 'UserOwnedMixin',
    'Paper', 'Tag', 'Note', 'Article', 'PaperVersion', 'WechatSubscription', 'WechatConfig',
    'UserPaperStatus',
    'paper_tags', 'note_tags', 'note_papers',
    'article_papers', 'article_tags', 'note_articles'
]
