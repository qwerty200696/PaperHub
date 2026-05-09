"""
笔记 API - 独立笔记 CRUD + 笔记-论文关联管理
"""
from flask import Blueprint, jsonify, request
from datetime import datetime

notes_bp = Blueprint('notes', __name__, url_prefix='/api/notes')


def get_note_routes(app):
    try:
        from backend.config import get_session
        from backend.models import Note, Paper, Article, Tag, note_papers, note_tags, note_articles
    except ImportError:
        from config import get_session
        from models import Note, Paper, Article, Tag, note_papers, note_tags, note_articles

    # ============================================================
    # 笔记 CRUD
    # ============================================================

    @notes_bp.route('', methods=['GET'])
    def list_notes():
        """获取笔记列表"""
        session = get_session()
        try:
            query = session.query(Note).filter(Note.is_deleted == False)

            keyword = request.args.get('q', '').strip()
            if keyword:
                query = query.filter(
                    (Note.title.contains(keyword)) |
                    (Note.content.contains(keyword))
                )

            source = request.args.get('source')
            if source:
                query = query.filter(Note.source == source)

            sort_by = request.args.get('sort', 'created_at')
            order_col = getattr(Note, sort_by, Note.created_at)
            query = query.order_by(order_col.desc())

            page = int(request.args.get('page', 1))
            per_page = int(request.args.get('per_page', 50))
            total = query.count()
            notes = query.offset((page - 1) * per_page).limit(per_page).all()

            return jsonify({
                'notes': [n.to_dict(include_papers=True, include_articles=True, include_tags=True) for n in notes],
                'total': total,
                'page': page,
                'per_page': per_page
            })
        finally:
            session.close()

    @notes_bp.route('', methods=['POST'])
    def create_note():
        """创建笔记"""
        session = get_session()
        try:
            try:
                from backend.services.note_deduplicator import check_note_duplicate
            except ImportError:
                from services.note_deduplicator import check_note_duplicate

            data = request.get_json() or {}
            title = data.get('title', '').strip() or None
            content = data.get('content', '')
            source = data.get('source', 'manual')
            url = data.get('url', '').strip() or None

            existing = check_note_duplicate(session, Note, title=title, content=content, url=url)
            if existing:
                return jsonify({
                    'error': '笔记已存在',
                    'duplicate': True,
                    'note_id': existing.id,
                    'note': existing.to_dict(include_papers=True)
                }), 409

            note = Note(
                title=title,
                content=content,
                source=source,
                url=url
            )
            session.add(note)
            session.flush()

            paper_ids = data.get('paper_ids', [])
            if not paper_ids:
                paper_id = data.get('paper_id')
                if paper_id:
                    paper_ids = [paper_id]

            for pid in paper_ids:
                paper = session.query(Paper).get(pid)
                if paper:
                    note.papers.append(paper)

            article_ids = data.get('article_ids', [])
            if not article_ids:
                article_id = data.get('article_id')
                if article_id:
                    article_ids = [article_id]

            try:
                from backend.models import Article
            except ImportError:
                from models import Article

            for aid in article_ids:
                article = session.query(Article).filter(Article.id == aid, Article.is_deleted == False).first()
                if article:
                    note.articles.append(article)

            tag_ids = data.get('tag_ids', [])
            for tid in tag_ids:
                tag = session.query(Tag).get(tid)
                if tag:
                    note.tags.append(tag)

            session.commit()
            return jsonify({'success': True, 'note': note.to_dict(include_papers=True), 'id': note.id}), 201
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>', methods=['GET'])
    def get_note(note_id):
        """获取笔记详情"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404
            _ = note.papers if hasattr(note, 'papers') else []
            _ = note.articles if hasattr(note, 'articles') else []
            _ = note.tags if hasattr(note, 'tags') else []
            return jsonify({
                'note': note.to_dict(include_papers=True, include_articles=True, include_tags=True)
            })
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>', methods=['PUT'])
    def update_note(note_id):
        """更新笔记"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            data = request.get_json() or {}
            if 'title' in data:
                note.title = data['title'].strip() or None
            if 'content' in data:
                note.content = data['content']
            if 'source' in data:
                note.source = data['source']
            if 'status' in data:
                note.status = data['status']
            if 'starred' in data:
                note.starred = data['starred']
            if 'pinned' in data:
                note.pinned = data['pinned']

            session.commit()
            return jsonify({'note': note.to_dict(include_papers=True)})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>', methods=['DELETE'])
    def delete_note(note_id):
        """删除笔记（硬删除）"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404
            session.delete(note)
            session.commit()
            return jsonify({'message': '删除成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # ============================================================
    # 笔记-论文关联管理
    # ============================================================

    @notes_bp.route('/<int:note_id>/papers', methods=['GET'])
    def list_note_papers(note_id):
        """获取某笔记关联的所有论文"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404
            return jsonify({
                'papers': [p.to_dict() for p in note.papers]
            })
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/papers', methods=['POST'])
    def link_note_paper(note_id):
        """关联笔记到论文"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            data = request.get_json() or {}
            paper_id = data.get('paper_id')
            if not paper_id:
                return jsonify({'error': '缺少 paper_id'}), 400

            paper = session.query(Paper).get(paper_id)
            if not paper:
                return jsonify({'error': '论文不存在'}), 404

            if paper not in note.papers:
                note.papers.append(paper)
                session.commit()

            return jsonify({'message': '关联成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/papers/<int:paper_id>', methods=['DELETE'])
    def unlink_note_paper(note_id, paper_id):
        """取消笔记-论文关联"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            paper = session.query(Paper).get(paper_id)
            if paper and paper in note.papers:
                note.papers.remove(paper)
                session.commit()

            return jsonify({'message': '取消关联成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # ============================================================
    # 笔记-标签管理
    # ============================================================

    @notes_bp.route('/<int:note_id>/tags', methods=['GET'])
    def list_note_tags(note_id):
        """获取笔记的所有标签"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404
            return jsonify({'tags': [t.to_dict() for t in note.tags]})
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/tags', methods=['POST'])
    def add_note_tag(note_id):
        """给笔记添加标签"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            data = request.get_json() or {}
            tag_id = data.get('tag_id')
            tag_name = data.get('name', '').strip()

            tag = None
            if tag_id:
                tag = session.query(Tag).get(tag_id)
            elif tag_name:
                tag = session.query(Tag).filter(Tag.name == tag_name).first()
                if not tag:
                    tag = Tag(name=tag_name)
                    session.add(tag)
                    session.flush()

            if tag and tag not in note.tags:
                note.tags.append(tag)
                session.commit()

            return jsonify({'tags': [t.to_dict() for t in note.tags]})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/tags/<int:tag_id>', methods=['DELETE'])
    def remove_note_tag(note_id, tag_id):
        """移除笔记的标签"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            tag = session.query(Tag).get(tag_id)
            if tag and tag in note.tags:
                note.tags.remove(tag)
                session.commit()

            return jsonify({'message': '移除标签成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # ============================================================
    # 笔记-文章关联管理
    # ============================================================

    @notes_bp.route('/<int:note_id>/articles', methods=['GET'])
    def list_note_articles(note_id):
        """获取某笔记关联的所有文章"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404
            return jsonify({
                'articles': [a.to_dict() for a in note.articles if not a.is_deleted]
            })
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/articles', methods=['POST'])
    def link_note_article(note_id):
        """关联笔记到文章"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            data = request.get_json() or {}
            article_id = data.get('article_id')
            if not article_id:
                return jsonify({'error': '缺少 article_id'}), 400

            article = session.query(Article).filter(
                Article.id == article_id,
                Article.is_deleted == False
            ).first()
            if not article:
                return jsonify({'error': '文章不存在'}), 404

            if article not in note.articles:
                note.articles.append(article)
                session.commit()

            return jsonify({'message': '关联成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    @notes_bp.route('/<int:note_id>/articles/<int:article_id>', methods=['DELETE'])
    def unlink_note_article(note_id, article_id):
        """取消笔记-文章关联"""
        session = get_session()
        try:
            note = session.query(Note).filter(
                Note.id == note_id,
                Note.is_deleted == False
            ).first()
            if not note:
                return jsonify({'error': '笔记不存在'}), 404

            article = session.query(Article).filter(Article.id == article_id, Article.is_deleted == False).first()
            if article and article in note.articles:
                note.articles.remove(article)
                session.commit()

            return jsonify({'message': '取消关联成功'})
        except Exception as e:
            session.rollback()
            return jsonify({'error': str(e)}), 500
        finally:
            session.close()

    # 注册蓝图
    app.register_blueprint(notes_bp)
