"""
PaperHub 数据模型
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, Date, Boolean, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship

try:
    from backend.models import Base
except ImportError:
    try:
        from models import Base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()


# ============================================================
# 论文-标签关联表 (多对多)
# ============================================================
paper_tags = Table(
    'paper_tags',
    Base.metadata,
    Column('paper_id', Integer, ForeignKey('papers.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 笔记-标签关联表 (多对多)
# ============================================================
note_tags = Table(
    'note_tags',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 文章-论文关联表 (多对多)
# ============================================================
article_papers = Table(
    'article_papers',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('paper_id', Integer, ForeignKey('papers.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 文章-标签关联表 (多对多)
# ============================================================
article_tags = Table(
    'article_tags',
    Base.metadata,
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 笔记-论文关联表 (多对多)
# ============================================================
note_papers = Table(
    'note_papers',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('paper_id', Integer, ForeignKey('papers.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 笔记-文章关联表 (多对多)
# ============================================================
note_articles = Table(
    'note_articles',
    Base.metadata,
    Column('note_id', Integer, ForeignKey('notes.id'), primary_key=True),
    Column('article_id', Integer, ForeignKey('articles.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.now)
)


# ============================================================
# 标签表
# ============================================================
class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False, unique=True)
    type = Column(String, nullable=False, default='custom')
    color = Column(String)
    parent_id = Column(Integer, ForeignKey('tags.id'))
    created_at = Column(DateTime, default=datetime.now)

    papers = relationship('Paper', secondary=paper_tags, back_populates='tags')
    notes = relationship('Note', secondary=note_tags, back_populates='tags')
    articles = relationship('Article', secondary=article_tags, back_populates='tags')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'type': self.type,
            'color': self.color,
            'parent_id': self.parent_id
        }


# ============================================================
# 论文/文章表
# ============================================================
class Paper(Base):
    __tablename__ = 'papers'

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
    authors = Column(Text)
    abstract = Column(Text)
    content = Column(Text)
    url = Column(String)
    source = Column(String, nullable=False)
    doi = Column(String)
    arxiv_id = Column(String)
    published_at = Column(Date)
    category_l1 = Column(String)
    category_l2 = Column(String)
    file_path = Column(String)
    save_local = Column(Boolean, default=True)
    status = Column(String, default='pending')
    starred = Column(Boolean, default=False)
    extra = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    tags = relationship('Tag', secondary=paper_tags, back_populates='papers')
    versions = relationship('PaperVersion', back_populates='paper', cascade='all, delete-orphan')
    notes = relationship('Note', secondary=note_papers, back_populates='papers')
    articles = relationship('Article', secondary=article_papers, back_populates='papers')

    def to_dict(self, include_articles=False, include_notes=False, include_tags=True):
        result = {
            'id': self.id,
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'content': self.content,
            'url': self.url,
            'source': self.source,
            'doi': self.doi,
            'arxiv_id': self.arxiv_id,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'category_l1': self.category_l1,
            'category_l2': self.category_l2,
            'file_path': self.file_path,
            'save_local': self.save_local,
            'status': self.status,
            'starred': self.starred,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'tags': [t.to_dict() for t in self.tags] if hasattr(self, 'tags') and include_tags else []
        }
        if include_articles and hasattr(self, 'articles'):
            result['articles'] = [{
                'id': a.id,
                'title': a.title,
                'author': a.author,
                'source': a.source,
                'published_at': a.published_at.isoformat() if a.published_at else None
            } for a in self.articles if not a.is_deleted]
        if include_notes and hasattr(self, 'notes'):
            result['notes'] = [{
                'id': n.id,
                'title': n.title,
                'source': n.source,
                'created_at': n.created_at.isoformat() if n.created_at else None
            } for n in self.notes]
        return result


# ============================================================
# 网络文章表（微信公众号、知乎、博客等）
# ============================================================
class Article(Base):
    __tablename__ = 'articles'

    id = Column(Integer, primary_key=True)
    title = Column(String(500), nullable=False)
    content = Column(Text)
    author = Column(String(200))
    source = Column(String(50), nullable=False)
    url = Column(String)
    file_path = Column(String)
    published_at = Column(Date)
    is_deleted = Column(Boolean, default=False)
    status = Column(String, default='pending')
    starred = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    papers = relationship('Paper', secondary=article_papers, back_populates='articles')
    tags = relationship('Tag', secondary=article_tags, back_populates='articles')
    notes = relationship('Note', secondary=note_articles, back_populates='articles')

    def to_dict(self, include_papers=False, include_notes=False, include_tags=True):
        result = {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'author': self.author,
            'source': self.source,
            'url': self.url,
            'file_path': self.file_path,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'is_deleted': self.is_deleted,
            'status': self.status,
            'starred': self.starred,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_tags:
            result['tags'] = [t.to_dict() for t in self.tags] if hasattr(self, 'tags') else []
        if include_papers:
            result['papers'] = [{
                'id': p.id,
                'title': p.title,
                'source': p.source,
                'published_at': p.published_at.isoformat() if p.published_at else None
            } for p in self.papers] if hasattr(self, 'papers') else []
        if include_notes and hasattr(self, 'notes'):
            result['notes'] = [{
                'id': n.id,
                'title': n.title or '',
                'source': n.source,
                'created_at': n.created_at.isoformat() if n.created_at else None
            } for n in self.notes if not n.is_deleted]
        return result


# ============================================================
# 笔记表（纯个人笔记、对话记录）
# ============================================================
class Note(Base):
    __tablename__ = 'notes'

    id = Column(Integer, primary_key=True)
    title = Column(String(500))
    content = Column(Text, nullable=False)
    source = Column(String(50), default='manual')
    url = Column(String)
    file_path = Column(String)
    published_at = Column(Date)
    is_deleted = Column(Boolean, default=False)
    status = Column(String, default='pending')
    starred = Column(Boolean, default=False)
    pinned = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    papers = relationship('Paper', secondary=note_papers, back_populates='notes')
    tags = relationship('Tag', secondary=note_tags, back_populates='notes')
    articles = relationship('Article', secondary=note_articles, back_populates='notes')

    def to_dict(self, include_papers=False, include_articles=False, include_tags=True):
        result = {
            'id': self.id,
            'title': self.title or '',
            'content': self.content,
            'source': self.source,
            'url': self.url,
            'file_path': self.file_path,
            'published_at': self.published_at.isoformat() if self.published_at else None,
            'is_deleted': self.is_deleted,
            'status': self.status,
            'starred': self.starred,
            'pinned': self.pinned if hasattr(self, 'pinned') else False,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
        if include_tags:
            result['tags'] = [t.to_dict() for t in self.tags] if hasattr(self, 'tags') else []
        if include_papers:
            result['papers'] = [p.to_dict(include_tags=True) for p in self.papers] if hasattr(self, 'papers') else []
        if include_articles and hasattr(self, 'articles'):
            result['articles'] = [a.to_dict(include_tags=True) for a in self.articles if not a.is_deleted]
        return result


# ============================================================
# 论文版本管理表
# ============================================================
class PaperVersion(Base):
    __tablename__ = 'paper_versions'

    id = Column(Integer, primary_key=True)
    paper_id = Column(Integer, ForeignKey('papers.id'), nullable=False)
    version = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    diff_summary = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    paper = relationship('Paper', back_populates='versions')

    def to_dict(self):
        return {
            'id': self.id,
            'paper_id': self.paper_id,
            'version': self.version,
            'file_path': self.file_path,
            'diff_summary': self.diff_summary,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class WechatSubscription(Base):
    __tablename__ = 'wechat_subscriptions'

    id = Column(Integer, primary_key=True)
    account_name = Column(String(200), nullable=False)
    account_id = Column(String(100))
    last_checked_at = Column(DateTime)
    last_post_time = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'account_name': self.account_name,
            'account_id': self.account_id,
            'last_checked_at': self.last_checked_at.isoformat() if self.last_checked_at else None,
            'last_post_time': self.last_post_time.isoformat() if self.last_post_time else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }


class WechatConfig(Base):
    __tablename__ = 'wechat_config'

    id = Column(Integer, primary_key=True)
    api_key = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def to_dict(self):
        return {
            'id': self.id,
            'api_key': self.api_key,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
