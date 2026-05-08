"""
Papers API - 论文相关 API
支持 arXiv 关键词搜索、分类筛选、批量导入
"""
from flask import Blueprint, jsonify, request, send_file, send_from_directory
from pathlib import Path
from datetime import datetime

bp = Blueprint('papers', __name__)


def get_session():
    """获取全局数据库 Session"""
    try:
        from backend.config import get_session as _get_session
    except ImportError:
        from config import get_session as _get_session
    return _get_session()


def get_models():
    try:
        from backend.models import Paper, Tag, Note, paper_tags
    except ImportError:
        from models import Paper, Tag, Note, paper_tags
    return Paper, Tag, Note, paper_tags


@bp.route('/papers', methods=['GET'])
def get_papers():
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    category_l1 = request.args.get('category_l1')
    status = request.args.get('status')
    starred = request.args.get('starred')
    tag_ids = request.args.get('tag_ids')
    source = request.args.get('source')
    published_date = request.args.get('published_date')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    year = request.args.get('year', type=int)
    month = request.args.get('month')

    Paper, _, _, _ = get_models()
    session = get_session()

    query = session.query(Paper)

    if category_l1:
        query = query.filter(Paper.category_l1 == category_l1)
    if status:
        query = query.filter(Paper.status == status)
    if starred is not None:
        query = query.filter(Paper.starred == (starred.lower() == 'true'))
    if source:
        query = query.filter(Paper.source == source)
    if published_date:
        from sqlalchemy import func
        query = query.filter(func.strftime('%Y-%m-%d', Paper.published_at) == published_date)
    if start_date:
        from sqlalchemy import func
        query = query.filter(func.strftime('%Y-%m-%d', Paper.published_at) >= start_date)
    if end_date:
        from sqlalchemy import func
        query = query.filter(func.strftime('%Y-%m-%d', Paper.published_at) <= end_date)
    if year:
        from sqlalchemy import func
        query = query.filter(func.strftime('%Y', Paper.published_at) == str(year))
    if month:
        from sqlalchemy import func
        query = query.filter(func.strftime('%Y-%m', Paper.published_at) == month)

    start_year = request.args.get('start_year', type=int)
    end_year = request.args.get('end_year', type=int)
    start_month = request.args.get('start_month')
    end_month = request.args.get('end_month')

    from sqlalchemy import func
    if start_year:
        query = query.filter(func.strftime('%Y', Paper.published_at) >= str(start_year))
    if end_year:
        query = query.filter(func.strftime('%Y', Paper.published_at) <= str(end_year))
    if start_month:
        query = query.filter(func.strftime('%Y-%m', Paper.published_at) >= start_month)
    if end_month:
        query = query.filter(func.strftime('%Y-%m', Paper.published_at) <= end_month)
    if tag_ids:
        _, _, _, paper_tags = get_models()
        tag_id_list = [int(t) for t in tag_ids.split(',') if t.isdigit()]
        for tag_id in tag_id_list:
            query = query.filter(Paper.tags.any(id=tag_id))

    query = query.order_by(Paper.created_at.desc())

    total = query.count()
    offset = (page - 1) * per_page
    papers = query.offset(offset).limit(per_page).all()

    for p in papers:
        _ = p.tags if hasattr(p, 'tags') else []

    return jsonify({
        'papers': [p.to_dict() for p in papers],
        'total': total,
        'page': page,
        'per_page': per_page,
        'pages': (total + per_page - 1) // per_page
    })


@bp.route('/papers/<int:paper_id>', methods=['GET'])
def get_paper(paper_id):
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR
    
    Paper, _, _, _ = get_models()
    session = get_session()

    paper = session.query(Paper).filter(Paper.id == paper_id).first()

    if not paper:
        return jsonify({'error': 'Not found'}), 404

    _ = paper.tags if hasattr(paper, 'tags') else []
    _ = paper.articles if hasattr(paper, 'articles') else []
    _ = paper.notes if hasattr(paper, 'notes') else []
    
    result = paper.to_dict(include_articles=True, include_notes=True)
    
    # 计算文件大小
    if paper.file_path:
        file_path = Path(paper.file_path)
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            # 转换为人类可读格式
            if size_bytes < 1024:
                result['file_size'] = f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                result['file_size'] = f"{size_bytes / 1024:.1f}KB"
            else:
                result['file_size'] = f"{size_bytes / (1024 * 1024):.1f}MB"
    
    return jsonify(result)


@bp.route('/papers/<int:paper_id>/notes', methods=['GET'])
def get_paper_notes(paper_id):
    """获取某论文关联的所有笔记"""
    Paper, _, Note, _ = get_models()
    session = get_session()
    try:
        paper = session.query(Paper).filter(Paper.id == paper_id).first()
        if not paper:
            return jsonify({'error': '论文不存在'}), 404

        notes = paper.notes
        notes_data = []
        for n in notes:
            if n.is_deleted:
                continue
            notes_data.append(n.to_dict(include_papers=False, include_tags=True))

        notes_data.sort(key=lambda x: (
            0 if x.get('pinned') else 1,
            0 if x.get('source') == 'AI解读' else 1,
            x.get('created_at', ''),
        ))

        return jsonify({
            'notes': notes_data,
            'total': len(notes_data)
        })
    finally:
        session.close()


@bp.route('/papers/<int:paper_id>', methods=['PUT'])
def update_paper(paper_id):
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR

    Paper, _, _, _ = get_models()
    session = get_session()

    paper = session.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return jsonify({'error': 'Not found'}), 404

    data = request.get_json()
    
    if 'save_local' in data and data['save_local'] != paper.save_local:
        new_save_local = data['save_local']
        
        if not new_save_local and paper.file_path:
            file_path = Path(paper.file_path)
            if not file_path.is_absolute():
                file_path = BASE_DIR / file_path
            if file_path.exists():
                try:
                    file_path.unlink()
                    paper.file_path = None
                except Exception as e:
                    print(f"Warning: Could not delete file: {e}")
        
        elif new_save_local and not paper.file_path and paper.url:
            try:
                try:
                    from backend.services import arxiv_fetcher
                except ImportError:
                    from services import arxiv_fetcher
                
                # 优先使用 arXiv 下载（如果有 arXiv ID）
                if paper.arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{paper.arxiv_id}.pdf"
                    file_path = arxiv_fetcher.download_pdf(pdf_url, paper.arxiv_id)
                else:
                    # 通用下载（用于非 arXiv 来源）
                    file_path = arxiv_fetcher.download_generic_pdf(paper.url, paper.id)
                
                paper.file_path = file_path
            except Exception as e:
                print(f"Warning: Could not download PDF: {e}")
    
    updatable_fields = ['title', 'authors', 'abstract', 'content', 'category_l1', 'category_l2', 'status', 'starred', 'arxiv_id', 'save_local', 'url', 'source']
    for field in updatable_fields:
        if field in data:
            setattr(paper, field, data[field])

    session.commit()
    _ = paper.tags if hasattr(paper, 'tags') else []
    result = paper.to_dict()
    
    # 计算文件大小
    if paper.file_path:
        file_path = Path(paper.file_path)
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path
        if file_path.exists():
            size_bytes = file_path.stat().st_size
            if size_bytes < 1024:
                result['file_size'] = f"{size_bytes}B"
            elif size_bytes < 1024 * 1024:
                result['file_size'] = f"{size_bytes / 1024:.1f}KB"
            else:
                result['file_size'] = f"{size_bytes / (1024 * 1024):.1f}MB"
    
    return jsonify(result)


@bp.route('/papers/<int:paper_id>', methods=['DELETE'])
def delete_paper(paper_id):
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR
    import shutil

    Paper, _, _, _ = get_models()
    session = get_session()

    paper = session.query(Paper).filter(Paper.id == paper_id).first()
    if not paper:
        return jsonify({'error': 'Paper not found'}), 404

    file_path = None
    if paper.file_path:
        file_path = Path(paper.file_path)
        if not file_path.is_absolute():
            file_path = BASE_DIR / file_path

    session.delete(paper)
    session.commit()

    if file_path and file_path.exists():
        try:
            if file_path.is_file():
                file_path.unlink()
            if paper.source == 'wechat':
                images_dir = file_path.parent / f"{file_path.stem}_files"
                if images_dir.exists() and images_dir.is_dir():
                    shutil.rmtree(images_dir)
            if paper.source == 'note' or paper.source == 'zhihu':
                md_file = file_path.parent / f"{file_path.stem}.md"
                if md_file.exists() and md_file.is_file():
                    md_file.unlink()
        except Exception as e:
            print(f"Warning: Could not delete file: {e}")

    return jsonify({'message': 'Paper deleted successfully', 'paper_id': paper_id}), 200


@bp.route('/papers/<int:paper_id>/images/<folder>/<filename>', methods=['GET'])
def serve_wechat_image(paper_id, folder, filename):
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR
    Paper, _, _, _ = get_models()
    session = get_session()

    paper = session.query(Paper).filter(Paper.id == paper_id).first()

    if not paper or not paper.file_path:
        return jsonify({'error': 'Paper not found'}), 404

    file_path = Path(paper.file_path)
    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path
    wechat_dir = file_path.parent
    image_path = wechat_dir / folder / filename

    if not image_path.exists():
        return jsonify({'error': 'Image not found'}), 404

    return send_file(str(image_path))


@bp.route('/papers/<int:paper_id>/download', methods=['GET'])
def download_paper(paper_id):
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR
    from flask import make_response

    Paper, _, _, _ = get_models()
    session = get_session()

    paper = session.query(Paper).filter(Paper.id == paper_id).first()

    if not paper or not paper.file_path:
        return jsonify({'error': 'File not found'}), 404

    file_path = Path(paper.file_path)
    if not file_path.is_absolute():
        file_path = BASE_DIR / file_path

    if not file_path.exists():
        wechat_dir = BASE_DIR / 'data/papers/wechat'
        for html_file in wechat_dir.glob('*.html'):
            if paper.title[:20] in html_file.stem or paper.arxiv_id and paper.arxiv_id in html_file.stem:
                file_path = html_file
                break

    if not file_path.exists():
        return jsonify({'error': 'File not found'}), 404

    if (paper.source == 'wechat' or paper.source == 'note' or paper.source == 'zhihu') and str(file_path).endswith('.html'):
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()

        if paper.source == 'wechat':
            base_dir = f'/api/papers/{paper_id}/images/'
            html_content = html_content.replace('<head>', f'<head><base href="{base_dir}">')

        response = make_response(html_content)
        response.headers['Content-Type'] = 'text/html; charset=utf-8'
        return response

    return send_file(str(file_path), as_attachment=False, download_name=f"{paper.title[:50]}.pdf")


@bp.route('/tags', methods=['GET'])
def get_all_tags():
    _, Tag, _, paper_tags = get_models()
    from sqlalchemy import func

    session = get_session()
    tags_with_count = session.query(
        Tag,
        func.count(paper_tags.c.paper_id).label('count')
    ).outerjoin(
        paper_tags, Tag.id == paper_tags.c.tag_id
    ).group_by(Tag.id).order_by(
        func.count(paper_tags.c.paper_id).desc(),
        Tag.name
    ).all()

    tags = []
    for tag, count in tags_with_count:
        tag_dict = tag.to_dict()
        tag_dict['count'] = count
        tags.append(tag_dict)

    return jsonify({'tags': tags})


@bp.route('/tags/articles', methods=['GET'])
def get_article_tags():
    _, Tag, _, _ = get_models()
    session = get_session()
    tags = session.query(Tag).order_by(Tag.name).all()
    return jsonify({'tags': [t.to_dict() for t in tags]})


@bp.route('/tags/notes', methods=['GET'])
def get_note_tags():
    _, Tag, _, _ = get_models()
    session = get_session()
    tags = session.query(Tag).order_by(Tag.name).all()
    return jsonify({'tags': [t.to_dict() for t in tags]})


@bp.route('/papers/<int:paper_id>/tags', methods=['POST'])
def add_tag_to_paper(paper_id):
    Paper, Tag, _, _ = get_models()

    session = get_session()
    paper = session.query(Paper).filter(Paper.id == paper_id).first()

    if not paper:
        return jsonify({'error': 'Paper not found'}), 404

    data = request.get_json()
    tag_name = data.get('name', '').strip()

    if not tag_name:
        return jsonify({'error': 'Tag name is required'}), 404

    tag = session.query(Tag).filter(Tag.name == tag_name).first()
    if not tag:
        tag = Tag(name=tag_name, type='custom')
        session.add(tag)
        session.flush()

    if tag not in paper.tags:
        paper.tags.append(tag)

    session.commit()
    return jsonify(paper.to_dict())


@bp.route('/papers/<int:paper_id>/tags/<int:tag_id>', methods=['DELETE'])
def remove_tag_from_paper(paper_id, tag_id):
    Paper, Tag, _, _ = get_models()

    session = get_session()
    paper = session.query(Paper).filter(Paper.id == paper_id).first()

    if not paper:
        return jsonify({'error': 'Paper not found'}), 404

    tag = session.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        return jsonify({'error': 'Tag not found'}), 404

    if tag in paper.tags:
        paper.tags.remove(tag)
        session.commit()

    return jsonify({'message': 'Tag removed successfully'})


@bp.route('/tags/<int:tag_id>', methods=['DELETE'])
def delete_tag(tag_id):
    _, Tag, _, _ = get_models()

    session = get_session()
    tag = session.query(Tag).filter(Tag.id == tag_id).first()

    if not tag:
        return jsonify({'error': 'Tag not found'}), 404

    session.delete(tag)
    session.commit()
    return jsonify({'message': 'Tag deleted successfully'})


@bp.route('/papers/search', methods=['GET'])
def search_arxiv():
    """
    搜索 arXiv 论文
    
    查询参数:
    - keywords: 关键词，逗号分隔（如 "machine learning,deep learning"）
    - categories: arXiv分类，逗号分隔（如 "cs.AI,stat.ML"）
    - max_results: 最大返回数量（默认20，最大100）
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）
    - sort_by: 排序方式（submittedDate/updatedDate/relevance，默认submittedDate）
    - sort_order: 排序顺序（ascending/descending，默认descending）
    """
    try:
        try:
            from backend.services import arxiv_fetcher
        except ImportError:
            from services import arxiv_fetcher
        
        # 获取查询参数
        keywords = request.args.get('keywords')
        categories = request.args.get('categories')
        max_results = request.args.get('max_results', 20, type=int)
        start_date_str = request.args.get('start_date')
        end_date_str = request.args.get('end_date')
        sort_by = request.args.get('sort_by', 'submittedDate')
        sort_order = request.args.get('sort_order', 'descending')
        
        # 限制最大返回数量
        max_results = min(max_results, 100)
        
        # 解析日期
        start_date = None
        end_date = None
        if start_date_str:
            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid start_date format. Use YYYY-MM-DD'}), 400
        if end_date_str:
            try:
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
            except ValueError:
                return jsonify({'error': 'Invalid end_date format. Use YYYY-MM-DD'}), 400
        
        # 解析关键词列表
        keyword_list = [k.strip() for k in keywords.split(',')] if keywords else None
        
        # 解析分类列表
        category_list = [c.strip() for c in categories.split(',')] if categories else None
        
        # 执行搜索
        results = arxiv_fetcher.search_arxiv_papers(
            keywords=keyword_list,
            categories=category_list,
            max_results=max_results,
            start_date=start_date,
            end_date=end_date,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        # 转换日期格式
        for paper in results:
            if paper.get('published_at'):
                paper['published_at'] = paper['published_at'].isoformat()
        
        return jsonify({
            'results': results,
            'total': len(results),
            'keywords': keywords,
            'categories': categories
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/papers/search/categories', methods=['GET'])
def get_arxiv_categories():
    """
    获取 arXiv 分类列表
    """
    try:
        try:
            from backend.services import arxiv_fetcher
        except ImportError:
            from services import arxiv_fetcher
        
        categories = arxiv_fetcher.get_arxiv_categories()
        
        # 按一级分类分组
        grouped_categories = {}
        for code, name in categories.items():
            if '.' in code:
                l1 = code.split('.')[0]
            else:
                l1 = code
            
            if l1 not in grouped_categories:
                grouped_categories[l1] = []
            grouped_categories[l1].append({
                'code': code,
                'name': name
            })
        
        return jsonify({
            'categories': categories,
            'grouped_categories': grouped_categories
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/papers/search/import', methods=['POST'])
def import_arxiv_papers():
    """
    批量导入 arXiv 论文到数据库
    
    请求体:
    {
        "papers": [
            {
                "arxiv_id": "2310.01234",
                "title": "...",
                "authors": ["..."],
                "abstract": "...",
                "pdf_url": "...",
                "categories": ["cs.AI"],
                "category_l1": "cs",
                "category_l2": "AI",
                "published_at": "2023-10-01",
                "doi": "..."
            }
        ],
        "save_pdf": true
    }
    """
    try:
        try:
            from backend.services import arxiv_fetcher
        except ImportError:
            from services import arxiv_fetcher
        
        Paper, _, _, _ = get_models()
        session = get_session()
        
        data = request.get_json()
        papers_data = data.get('papers', [])
        save_pdf = data.get('save_pdf', False)
        
        imported_count = 0
        skipped_count = 0
        errors = []
        
        for paper_info in papers_data:
            arxiv_id = paper_info.get('arxiv_id')
            
            # 检查是否已存在
            existing_paper = session.query(Paper).filter(
                Paper.arxiv_id == arxiv_id
            ).first()
            
            if existing_paper:
                skipped_count += 1
                continue
            
            # 创建新论文记录
            try:
                authors_str = ', '.join(paper_info.get('authors', []))
                
                published_at = None
                if paper_info.get('published_at'):
                    try:
                        published_at = datetime.strptime(paper_info['published_at'], '%Y-%m-%d').date()
                    except ValueError:
                        pass
                
                paper = Paper(
                    title=paper_info['title'],
                    authors=authors_str,
                    abstract=paper_info.get('abstract'),
                    url=paper_info.get('url'),
                    source='arxiv',
                    doi=paper_info.get('doi'),
                    arxiv_id=arxiv_id,
                    published_at=published_at,
                    category_l1=paper_info.get('category_l1'),
                    category_l2=paper_info.get('category_l2'),
                    status='pending',
                    save_local=save_pdf
                )
                
                session.add(paper)
                session.flush()
                
                # 下载 PDF（如果需要）
                if save_pdf and paper_info.get('pdf_url'):
                    try:
                        file_path = arxiv_fetcher.download_pdf(paper_info['pdf_url'], arxiv_id)
                        paper.file_path = file_path
                    except Exception as download_error:
                        errors.append(f"Failed to download PDF for {arxiv_id}: {str(download_error)}")
                
                imported_count += 1
            
            except Exception as e:
                errors.append(f"Failed to import {arxiv_id}: {str(e)}")
                session.rollback()
        
        session.commit()
        
        return jsonify({
            'imported': imported_count,
            'skipped': skipped_count,
            'errors': errors
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500