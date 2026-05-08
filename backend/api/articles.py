"""
文章库 API
处理微信公众号、知乎文章等网络文章的CRUD和关联管理
"""
from flask import Blueprint, request, jsonify

bp = Blueprint('articles', __name__, url_prefix='/api/articles')


def get_session():
    """获取全局数据库 Session"""
    try:
        from backend.config import get_session as _get_session
    except ImportError:
        from config import get_session as _get_session
    return _get_session()


def get_article_routes(app):
    try:
        from backend.models import Article, Paper
    except ImportError:
        from models import Article, Paper

    @bp.route('', methods=['GET'])
    def list_articles():
        """获取文章列表"""
        session = get_session()
        try:
            source = request.args.get('source')
            search = request.args.get('search', '').strip()

            query = session.query(Article).filter(Article.is_deleted == False)

            if source:
                query = query.filter(Article.source == source)

            if search:
                query = query.filter(
                    (Article.title.contains(search)) |
                    (Article.author.contains(search)) |
                    (Article.content.contains(search))
                )

            articles = query.order_by(Article.created_at.desc()).all()

            return jsonify({
                'articles': [a.to_dict(include_papers=True, include_notes=True, include_tags=True) for a in articles],
                'total': len(articles)
            }), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>', methods=['GET'])
    def get_article(article_id):
        """获取单个文章"""
        session = get_session()
        try:
            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            _ = article.tags if hasattr(article, 'tags') else []
            _ = article.papers if hasattr(article, 'papers') else []
            _ = article.notes if hasattr(article, 'notes') else []
            return jsonify({
                'article': article.to_dict(include_papers=True, include_notes=True, include_tags=True)
            }), 200

        finally:
            session.close()

    @bp.route('', methods=['POST'])
    def create_article():
        """创建文章"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400

        if not data.get('title'):
            return jsonify({'error': 'Title is required'}), 400

        if not data.get('source'):
            return jsonify({'error': 'Source is required'}), 400

        session = get_session()
        try:
            try:
                from backend.services.article_deduplicator import check_article_duplicate
            except ImportError:
                from services.article_deduplicator import check_article_duplicate

            title = data['title']
            content = data.get('content', '')
            url = data.get('url')

            existing = check_article_duplicate(session, Article, title=title, content=content, url=url)
            if existing:
                return jsonify({
                    'error': '文章已存在',
                    'duplicate': True,
                    'article_id': existing.id,
                    'article': existing.to_dict(include_papers=True)
                }), 409

            article = Article(
                title=data['title'],
                content=data.get('content', ''),
                author=data.get('author'),
                source=data['source'],
                url=data.get('url'),
                file_path=data.get('file_path'),
                published_at=data.get('published_at')
            )

            session.add(article)
            session.commit()
            session.refresh(article)

            return jsonify({
                'message': 'Article created successfully',
                'article': article.to_dict(include_papers=True, include_tags=True)
            }), 201

        finally:
            session.close()

    @bp.route('/<int:article_id>', methods=['PUT'])
    def update_article(article_id):
        """更新文章"""
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Missing request body'}), 400

        session = get_session()
        try:
            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            updatable_fields = ['title', 'content', 'author', 'url', 'file_path', 'published_at', 'status', 'starred']
            for field in updatable_fields:
                if field in data:
                    if field == 'published_at' and data[field]:
                        from datetime import datetime
                        try:
                            setattr(article, field, datetime.strptime(data[field], '%Y-%m-%d').date())
                        except ValueError:
                            pass
                    else:
                        setattr(article, field, data[field])

            session.commit()

            return jsonify({
                'message': 'Article updated successfully',
                'article': article.to_dict(include_papers=True, include_tags=True)
            }), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>', methods=['DELETE'])
    def delete_article(article_id):
        """删除文章（软删除）"""
        session = get_session()
        try:
            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            article.is_deleted = True
            session.commit()

            return jsonify({'message': 'Article deleted successfully'}), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>/papers', methods=['POST'])
    def link_paper_to_article(article_id):
        """关联论文到文章"""
        data = request.get_json()
        if not data or 'paper_id' not in data:
            return jsonify({'error': 'paper_id is required'}), 400

        session = get_session()
        try:
            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            paper = session.query(Paper).filter(Paper.id == data['paper_id']).first()
            if not paper:
                return jsonify({'error': 'Paper not found'}), 404

            if paper not in article.papers:
                article.papers.append(paper)
                session.commit()

            return jsonify({
                'message': 'Paper linked successfully',
                'article': article.to_dict(include_papers=True, include_tags=True)
            }), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>/papers/<int:paper_id>', methods=['DELETE'])
    def unlink_paper_from_article(article_id, paper_id):
        """取消文章关联的论文"""
        session = get_session()
        try:
            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            paper = session.query(Paper).filter(Paper.id == paper_id).first()
            if not paper:
                return jsonify({'error': 'Paper not found'}), 404

            if paper in article.papers:
                article.papers.remove(paper)
                session.commit()

            return jsonify({
                'message': 'Paper unlinked successfully',
                'article': article.to_dict(include_papers=True, include_tags=True)
            }), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>/tags', methods=['POST'])
    def add_tag_to_article(article_id):
        """给文章添加标签"""
        session = get_session()
        try:
            try:
                from backend.models import Article, Tag
            except ImportError:
                from models import Article, Tag

            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            data = request.get_json()
            tag_name = data.get('name', '').strip()

            if not tag_name:
                return jsonify({'error': 'Tag name is required'}), 400

            tag = session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, type='custom')
                session.add(tag)
                session.flush()

            if tag not in article.tags:
                article.tags.append(tag)

            session.commit()
            return jsonify({
                'message': 'Tag added successfully',
                'article': article.to_dict(include_papers=True, include_tags=True)
            }), 200

        finally:
            session.close()

    @bp.route('/<int:article_id>/tags/<int:tag_id>', methods=['DELETE'])
    def remove_tag_from_article(article_id, tag_id):
        """移除文章的标签"""
        session = get_session()
        try:
            try:
                from backend.models import Article, Tag
            except ImportError:
                from models import Article, Tag

            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()

            if not article:
                return jsonify({'error': 'Article not found'}), 404

            tag = session.query(Tag).filter(Tag.id == tag_id).first()
            if not tag:
                return jsonify({'error': 'Tag not found'}), 404

            if tag in article.tags:
                article.tags.remove(tag)
                session.commit()

            return jsonify({
                'message': 'Tag removed successfully'
            }), 200

        finally:
            session.close()

    app.register_blueprint(bp)
