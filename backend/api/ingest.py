"""
Ingest API - 入库 API
"""
import json
import uuid
from pathlib import Path
from flask import Blueprint, jsonify, request
from werkzeug.utils import secure_filename

bp = Blueprint('ingest', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'html', 'htm'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_session():
    """获取全局数据库 Session"""
    try:
        from backend.config import get_session as _get_session
    except ImportError:
        from config import get_session as _get_session
    return _get_session()


def get_models():
    try:
        from backend.models import Paper, Note, Article
    except ImportError:
        from models import Paper, Note, Article
    return Paper, Note, Article


@bp.route('/ingest/arxiv/search', methods=['GET'])
def search_arxiv():
    """
    搜索 arXiv 论文
    
    Query Parameters:
    - keywords: 关键词（逗号分隔）
    - max_results: 返回数量（默认10）
    - categories: 分类筛选（逗号分隔）
    - start_date: 开始日期（YYYY-MM-DD）
    - end_date: 结束日期（YYYY-MM-DD）
    """
    keywords = request.args.get('keywords', '')
    max_results = int(request.args.get('max_results', 10))
    categories = request.args.get('categories', '')
    start_date = request.args.get('start_date', '')
    end_date = request.args.get('end_date', '')

    try:
        from services import arxiv_fetcher
    except ImportError:
        from backend.services import arxiv_fetcher

    try:
        # 解析关键词
        keyword_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else None

        # 解析分类
        category_list = [c.strip() for c in categories.split(',') if c.strip()] if categories else None

        # 解析日期
        start_date_obj = None
        end_date_obj = None
        if start_date:
            from datetime import datetime
            start_date_obj = datetime.strptime(start_date, '%Y-%m-%d').date()
        if end_date:
            from datetime import datetime
            end_date_obj = datetime.strptime(end_date, '%Y-%m-%d').date()

        results = arxiv_fetcher.search_arxiv_papers(
            keywords=keyword_list,
            categories=category_list,
            max_results=max_results,
            start_date=start_date_obj,
            end_date=end_date_obj
        )

        return jsonify(results), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/arxiv/batch', methods=['POST'])
def ingest_arxiv_batch():
    """
    批量导入 arXiv 论文
    
    Request JSON:
    {
        "arxiv_ids": ["2604.08224", "2604.12345"],
        "download_pdf": true
    }
    """
    data = request.get_json()
    if not data or 'arxiv_ids' not in data:
        return jsonify({'error': 'Missing arxiv_ids parameter'}), 400

    arxiv_ids = data['arxiv_ids']
    download_pdf = data.get('download_pdf', True)

    if not isinstance(arxiv_ids, list) or len(arxiv_ids) == 0:
        return jsonify({'error': 'arxiv_ids must be a non-empty list'}), 400

    try:
        from services import arxiv_fetcher, deduplicator
    except ImportError:
        from backend.services import arxiv_fetcher, deduplicator

    Paper, Note, Article = get_models()
    session = get_session()

    success_count = 0
    failed_count = 0
    errors = []

    for arxiv_id in arxiv_ids:
        try:
            # 检查是否已存在
            existing = session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
            if existing:
                continue

            paper_data = arxiv_fetcher.fetch_arxiv_paper(arxiv_id)

            duplicate = deduplicator.check_duplicate(
                session, Paper,
                title=paper_data['title'],
                doi=paper_data['doi'],
                arxiv_id=arxiv_id,
                url=f"https://arxiv.org/abs/{arxiv_id}"
            )
            if duplicate:
                continue

            file_path = None
            content = None
            if download_pdf:
                file_path = arxiv_fetcher.download_pdf(paper_data['pdf_url'], arxiv_id)
                content = arxiv_fetcher.extract_pdf_text(file_path)

            paper = Paper(
                title=paper_data['title'],
                authors=json.dumps(paper_data['authors'], ensure_ascii=False),
                abstract=paper_data['abstract'],
                content=content,
                url=f"https://arxiv.org/abs/{arxiv_id}",
                source='arxiv',
                doi=paper_data['doi'],
                arxiv_id=arxiv_id,
                published_at=paper_data['published_at'],
                file_path=file_path,
                save_local=download_pdf,
                status='pending',
                starred=False
            )

            session.add(paper)
            success_count += 1

        except Exception as e:
            failed_count += 1
            errors.append({'arxiv_id': arxiv_id, 'error': str(e)})

    session.commit()

    return jsonify({
        'message': f'Successfully ingested {success_count}/{len(arxiv_ids)} papers',
        'count': success_count,
        'failed': failed_count,
        'errors': errors
    }), 200


@bp.route('/ingest/arxiv', methods=['POST'])
def ingest_arxiv():
    data = request.get_json()
    if not data or 'input' not in data:
        return jsonify({'error': 'Missing input parameter'}), 400

    try:
        from services import arxiv_fetcher, deduplicator
    except ImportError:
        from backend.services import arxiv_fetcher, deduplicator

    try:
        arxiv_id = arxiv_fetcher.parse_arxiv_input(data['input'])

        Paper, Note, Article = get_models()
        session = get_session()

        existing = session.query(Paper).filter(Paper.arxiv_id == arxiv_id).first()
        if existing:
            return jsonify({
                'error': 'Paper already exists',
                'paper_id': existing.id,
                'paper': existing.to_dict()
            }), 409

        paper_data = arxiv_fetcher.fetch_arxiv_paper(arxiv_id)

        duplicate = deduplicator.check_duplicate(
            session, Paper,
            title=paper_data['title'],
            doi=paper_data['doi'],
            arxiv_id=arxiv_id,
            url=f"https://arxiv.org/abs/{arxiv_id}"
        )
        if duplicate:
            return jsonify({
                'error': 'Paper already exists',
                'duplicate_type': 'arxiv_id/title/doi',
                'paper_id': duplicate.id,
                'paper': duplicate.to_dict()
            }), 409

        file_path = arxiv_fetcher.download_pdf(paper_data['pdf_url'], arxiv_id)
        content = arxiv_fetcher.extract_pdf_text(file_path)

        paper = Paper(
            title=paper_data['title'],
            authors=json.dumps(paper_data['authors'], ensure_ascii=False),
            abstract=paper_data['abstract'],
            content=content,
            url=f"https://arxiv.org/abs/{arxiv_id}",
            source='arxiv',
            doi=paper_data['doi'],
            arxiv_id=arxiv_id,
            published_at=paper_data['published_at'],
            file_path=file_path,
            save_local=True,
            status='pending',
            starred=False
        )

        session.add(paper)
        session.commit()
        session.refresh(paper)

        return jsonify({
            'message': 'Paper ingested successfully',
            'paper': paper.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/note', methods=['POST'])
def ingest_note():
    """
    导入对话笔记/大模型对话内容 - 导入到笔记库

    Request JSON:
    {
        "title": "文章标题",
        "source": "Claude 对话 / ChatGPT / ...",
        "content": "Markdown 格式的正文内容",
        "created_at": "2026-04-30T12:00:00" 可选，默认当前时间
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    required_fields = ['title', 'source', 'content']
    for field in required_fields:
        if field not in data or not data[field].strip():
            return jsonify({'error': f'Missing required field: {field}'}), 400

    title = data['title'].strip()
    source = data['source'].strip()
    content = data['content'].strip()

    created_at = None
    if data.get('created_at'):
        try:
            from datetime import datetime
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        except:
            pass

    try:
        try:
            from services import note_importer
        except ImportError:
            from backend.services import note_importer

        note_data = note_importer.save_note(title, source, content, created_at)

        Paper, Note, Article = get_models()
        session = get_session()

        try:
            from backend.services.note_deduplicator import check_note_duplicate
        except ImportError:
            from services.note_deduplicator import check_note_duplicate

        existing_note = check_note_duplicate(
            session, Note,
            title=note_data['title'],
            content=note_data['content'],
            url=note_data['source_url']
        )
        if existing_note:
            return jsonify({
                'error': 'Note already exists',
                'note_id': existing_note.id,
                'note': existing_note.to_dict()
            }), 409

        note = Note(
            title=note_data['title'],
            content=note_data['content'],
            source=source,
            url=note_data['source_url'],
            published_at=note_data['published_at'],
            file_path=note_data['file_path']
        )

        session.add(note)
        session.commit()
        session.refresh(note)

        return jsonify({
            'message': 'Note ingested successfully',
            'note': note.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/zhihu', methods=['POST'])
def ingest_zhihu():
    """
    导入知乎专栏文章 - 导入到文章库

    模式 1 - URL 自动导入:
    {
        "url": "https://zhuanlan.zhihu.com/p/xxx",
        "cookie": "浏览器复制的知乎Cookie"
    }

    模式 2 - 手动粘贴内容:
    {
        "title": "文章标题",
        "author": "知乎作者名称",
        "content": "Markdown 格式的正文内容",
        "created_at": "2026-04-30T12:00:00" 可选，默认当前时间
    }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': 'Missing request body'}), 400

    Paper, Note, Article = get_models()
    session = get_session()

    try:
        try:
            from services import note_importer, zhihu_parser
        except ImportError:
            from backend.services import note_importer, zhihu_parser
    except ImportError:
        from services import note_importer
        zhihu_parser = None

    try:
        if data.get('url') and data.get('cookie') and zhihu_parser:
            url = data['url'].strip()
            cookie = data['cookie'].strip()

            if not url or not cookie:
                return jsonify({'error': 'URL 和 Cookie 不能为空'}), 400

            article_data = zhihu_parser.save_zhihu_article(url, cookie)
            source_url = url
            file_path = article_data['file_path']
            published_at = article_data['published_at']
            title = article_data['title']
            content = article_data['content']
        else:
            required_fields = ['title', 'content']
            for field in required_fields:
                if field not in data or not data[field].strip():
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            title = data['title'].strip()
            author = data.get('author', '知乎专栏').strip()
            content = data['content'].strip()

            created_at = None
            if data.get('created_at'):
                try:
                    from datetime import datetime
                    created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
                except:
                    pass

            article_data = note_importer.save_note(title, f'知乎 · {author}', content, created_at, subfolder='zhihu')
            source_url = article_data['source_url']
            file_path = article_data['file_path']
            published_at = article_data['published_at']

        try:
            from backend.services.article_deduplicator import check_article_duplicate
        except ImportError:
            from services.article_deduplicator import check_article_duplicate

        existing_article = check_article_duplicate(
            session, Article,
            title=title,
            content=content,
            url=source_url
        )
        if existing_article:
            return jsonify({
                'error': 'Article already exists',
                'article_id': existing_article.id,
                'article': existing_article.to_dict()
            }), 409

        article = Article(
            title=title,
            content=content,
            author=author if not data.get('url') else article_data.get('author', '知乎专栏'),
            source='zhihu',
            url=source_url,
            published_at=published_at,
            file_path=file_path
        )

        session.add(article)
        session.commit()
        session.refresh(article)

        return jsonify({
            'message': 'Zhihu article ingested successfully',
            'article': article.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/pdf', methods=['POST'])
def ingest_pdf():
    try:
        from backend.config import BASE_DIR
    except ImportError:
        from config import BASE_DIR
    from datetime import date

    if 'file' not in request.files:
        return jsonify({'error': 'No files uploaded'}), 400

    files = request.files.getlist('file')
    if not files or files[0].filename == '':
        return jsonify({'error': 'No files selected'}), 400

    pdf_url = request.form.get('pdf_url', '').strip()

    results = []
    Paper, Note, Article = get_models()
    session = get_session()

    try:
        from services import pdf_processor, wechat_parser, deduplicator, article_deduplicator
    except ImportError:
        from backend.services import pdf_processor, wechat_parser, deduplicator, article_deduplicator

    check_article_duplicate = article_deduplicator.check_article_duplicate

    for file in files:
        if file and allowed_file(file.filename):
            try:
                filename = secure_filename(file.filename)
                unique_id = str(uuid.uuid4())[:8]
                save_filename = f"{unique_id}_{filename}"
                relative_path = f"data/papers/uploaded/{save_filename}"
                full_path = BASE_DIR / relative_path
                full_path.parent.mkdir(parents=True, exist_ok=True)

                file.save(str(full_path))

                is_html = filename.lower().endswith('.html') or filename.lower().endswith('.htm')

                if is_html:
                    article_data = wechat_parser.parse_local_html(str(full_path))

                    existing_article = check_article_duplicate(
                        session, Article,
                        title=article_data['title'],
                        content=article_data['content'],
                        url=article_data['source_url']
                    )
                    if existing_article:
                        Path(full_path).unlink(missing_ok=True)
                        results.append({
                            'filename': filename,
                            'status': 'duplicate',
                            'article_id': existing_article.id,
                            'title': existing_article.title,
                            'message': f'Duplicate detected: {existing_article.title[:50]}...'
                        })
                        continue

                    Path(full_path).unlink(missing_ok=True)

                    article = Article(
                        title=article_data['title'],
                        content=article_data['content'],
                        author=article_data.get('account_name', '微信公众号'),
                        source='wechat',
                        url=article_data['source_url'],
                        published_at=article_data['published_at'],
                        file_path=article_data['file_path']
                    )

                    session.add(article)
                    session.flush()

                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'article_id': article.id,
                        'title': article.title
                    })
                else:
                    existing = session.query(Paper).filter(Paper.file_path == relative_path).first()
                    if existing:
                        results.append({
                            'filename': filename,
                            'status': 'duplicate',
                            'paper_id': existing.id,
                            'message': 'File already exists'
                        })
                        continue

                    pdf_data = pdf_processor.process_pdf_file(str(full_path), filename)

                    duplicate = deduplicator.check_duplicate(
                        session, Paper,
                        title=pdf_data['title']
                    )
                    if duplicate:
                        Path(full_path).unlink(missing_ok=True)
                        results.append({
                            'filename': filename,
                            'status': 'duplicate',
                            'paper_id': duplicate.id,
                            'title': duplicate.title,
                            'message': f'Duplicate detected: {duplicate.title[:50]}...'
                        })
                        continue

                    paper = Paper(
                        title=pdf_data['title'],
                        authors=json.dumps(pdf_data['authors'], ensure_ascii=False),
                        abstract=pdf_data['abstract'],
                        content=pdf_data['content'],
                        source='pdf',
                        url=pdf_url if pdf_url else None,
                        published_at=date.today(),
                        file_path=relative_path,
                        save_local=True,
                        status='pending',
                        starred=False
                    )

                    session.add(paper)
                    session.flush()

                    results.append({
                        'filename': filename,
                        'status': 'success',
                        'paper_id': paper.id,
                        'title': paper.title
                    })

            except Exception as e:
                import traceback
                traceback.print_exc()
                results.append({
                    'filename': file.filename,
                    'status': 'error',
                    'error': str(e)
                })

    session.commit()

    success_count = sum(1 for r in results if r['status'] == 'success')
    return jsonify({
        'message': f'Successfully ingested {success_count}/{len(results)} files',
        'success': success_count,
        'total': len(results),
        'results': results
    }), 200


@bp.route('/ingest/wechat/local', methods=['POST'])
def ingest_wechat_local():
    data = request.get_json()
    if not data or 'html_path' not in data:
        return jsonify({'error': 'Missing html_path parameter'}), 400

    html_path = data['html_path'].strip()
    assets_folder = data.get('assets_folder', None)
    from pathlib import Path

    if not Path(html_path).exists():
        return jsonify({'error': 'HTML 文件不存在'}), 400

    try:
        try:
            from services import wechat_parser
        except ImportError:
            from backend.services import wechat_parser
        article_data = wechat_parser.parse_local_html(html_path, assets_folder)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'解析失败: {str(e)}'}), 500

    Paper, Note, Article = get_models()
    session = get_session()

    try:
        from backend.services.article_deduplicator import check_article_duplicate
    except ImportError:
        from services.article_deduplicator import check_article_duplicate

    existing_article = check_article_duplicate(
        session, Article,
        title=article_data['title'],
        content=article_data['content'],
        url=article_data['source_url']
    )
    if existing_article:
        return jsonify({
            'article_id': existing_article.id,
            'title': existing_article.title,
            'duplicate': True,
            'message': 'Duplicate detected'
        }), 200

    article = Article(
        title=article_data['title'],
        content=article_data['content'],
        author=article_data.get('account_name', '微信公众号'),
        source='wechat',
        url=article_data['source_url'],
        published_at=article_data['published_at'],
        file_path=article_data['file_path']
    )

    session.add(article)
    session.commit()
    session.refresh(article)

    return jsonify({
        'article_id': article.id,
        'title': article.title,
        'message': 'Success'
    }), 200


@bp.route('/ingest/wechat', methods=['POST'])
def ingest_wechat():
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing url parameter'}), 400

    url = data['url'].strip()
    extract_content_only = data.get('extract_content_only', False)
    try:
        from services import wechat_parser
    except ImportError:
        from backend.services import wechat_parser

    if not wechat_parser.is_wechat_url(url):
        return jsonify({'error': '不是有效的微信公众号链接'}), 400

    Paper, Note, Article = get_models()
    session = get_session()

    try:
        from backend.services.article_deduplicator import check_article_duplicate
    except ImportError:
        from services.article_deduplicator import check_article_duplicate

    try:
        article_data = wechat_parser.fetch_wechat_article_new(url, 'html')

        if not article_data:
            return jsonify({'error': '获取文章内容失败'}), 500

        existing_article = check_article_duplicate(
            session, Article,
            title=article_data['title'],
            content=article_data['content'],
            url=url
        )
        if existing_article:
            return jsonify({
                'error': 'Article already exists',
                'article_id': existing_article.id,
                'article': existing_article.to_dict()
            }), 409

        file_path = article_data.get('file_path')

        article = Article(
            title=article_data['title'],
            content=article_data['content'],
            author=article_data.get('account_name', '微信公众号'),
            source='wechat',
            url=url,
            published_at=article_data['published_at'],
            file_path=file_path
        )

        session.add(article)
        session.commit()
        session.refresh(article)

        return jsonify({
            'message': 'Article ingested successfully',
            'article': article.to_dict()
        }), 201

    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/web/preview', methods=['POST'])
def preview_web_article():
    """
    预览通用网页 - 不直接入库，返回提取结果让用户编辑
    Request JSON: { "url": "https://example.com/article" }
    """
    data = request.get_json()
    if not data or 'url' not in data:
        return jsonify({'error': 'Missing url parameter'}), 400
    
    url = data['url'].strip()
    if not url:
        return jsonify({'error': 'url不能为空'}), 400
    
    Paper, Note, Article = get_models()
    session = get_session()
    
    try:
        try:
            from backend.services.web_parser import UniversalWebParser
        except ImportError:
            from services.web_parser import UniversalWebParser
        
        parser = UniversalWebParser()
        extract_result = parser.extract_article(url)
        
        if not extract_result.get('success') and not extract_result.get('text'):
            return jsonify({'error': '网页正文提取失败'}), 400
        
        return jsonify({
            'message': 'Preview success',
            'url': url,
            'title': extract_result.get('title', ''),
            'author': extract_result.get('author', ''),
            'content': extract_result.get('text', ''),
            'html': extract_result.get('html', ''),
            'text_length': extract_result.get('text_length', 0),
            'html_length': extract_result.get('html_length', 0),
            'best_method': extract_result.get('best_method', '')
        }), 200
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/web', methods=['POST'])
def ingest_web_general():
    """
    入库通用网页 - 经过用户确认后的内容
    Request JSON: {
        "url": "https://example.com/article",
        "title": "编辑后的标题",
        "author": "编辑后的作者",
        "content": "编辑后的纯文本正文内容",
        "html": "编辑后的HTML正文内容（优先使用）"
    }
    """
    data = request.get_json() or {}
    
    url = data.get('url', '').strip()
    title = data.get('title', '').strip()
    author = data.get('author', '通用网页').strip()
    content = data.get('content', '').strip()
    html_content = data.get('html', '').strip()
    
    if not url or not title:
        return jsonify({'error': 'url and title are required'}), 400
    
    final_content = html_content if html_content else content
    if not final_content:
        return jsonify({'error': 'content or html is required'}), 400
    
    Paper, Note, Article = get_models()
    session = get_session()
    
    try:
        try:
            from backend.config import BASE_DIR
            from backend.services.web_parser import UniversalWebParser
        except ImportError:
            from config import BASE_DIR
            from services.web_parser import UniversalWebParser
        
        try:
            from backend.services.article_deduplicator import check_article_duplicate
        except ImportError:
            from services.article_deduplicator import check_article_duplicate
        check_article_duplicate_func = check_article_duplicate
        
        existing_article = check_article_duplicate_func(
            session, Article,
            title=title,
            content=final_content,
            url=url
        )
        if existing_article:
            return jsonify({
                'error': 'Article already exists',
                'duplicate': True,
                'article_id': existing_article.id,
                'article': existing_article.to_dict()
            }), 409
        
        import uuid
        import re
        import requests
        from bs4 import BeautifulSoup
        import urllib.parse
        parsed = urllib.parse.urlparse(url)
        safe_name = re.sub(r'[^\w\-.]', '_', parsed.netloc + parsed.path)
        article_id = str(uuid.uuid4())[:8]
        save_filename = f"{article_id}_{safe_name}"
        if not save_filename.endswith('.html'):
            save_filename += '.html'
        relative_path = f"data/papers/web/{save_filename}"
        full_path = BASE_DIR / relative_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        images_dir = full_path.parent / f'{article_id}_files'
        images_dir.mkdir(exist_ok=True)
        
        local_html_content = final_content
        downloaded_images_count = 0
        if html_content:
            try:
                soup = BeautifulSoup(html_content, 'lxml')
                USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
                
                for i, img in enumerate(soup.find_all('img')):
                    img_url = img.get('src', '') or img.get('data-src', '')
                    local_file = None
                    
                    if img_url:
                        if not img_url.startswith('http'):
                            img_url = urllib.parse.urljoin(url, img_url)
                        
                        if img_url.startswith('http'):
                            try:
                                headers = {'User-Agent': USER_AGENT, 'Referer': url}
                                img_resp = requests.get(img_url, headers=headers, timeout=10)
                                if img_resp.status_code == 200:
                                    ext = '.png'
                                    lower_url = img_url.lower()
                                    if '.gif' in lower_url:
                                        ext = '.gif'
                                    elif '.jpg' in lower_url or '.jpeg' in lower_url:
                                        ext = '.jpg'
                                    elif '.webp' in lower_url:
                                        ext = '.webp'
                                    local_file = f'{i}{ext}'
                                    with open(images_dir / local_file, 'wb') as f:
                                        f.write(img_resp.content)
                                    downloaded_images_count += 1
                            except Exception as e:
                                pass
                    
                    if local_file:
                        img['src'] = f'/static/web/{article_id}_files/{local_file}'
                    else:
                        if img.parent:
                            img.decompose()
                
                local_html_content = str(soup)
            except Exception as e:
                pass
        
        parser = UniversalWebParser()
        try:
            raw_html, _ = parser.fetch_html(url)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(raw_html)
        except Exception:
            pass
        
        from datetime import date
        article = Article(
            title=title,
            content=local_html_content if html_content else final_content,
            author=author,
            source='web',
            url=url,
            published_at=date.today(),
            file_path=str(full_path)
        )
        
        session.add(article)
        session.commit()
        session.refresh(article)
        
        return jsonify({
            'message': 'Web article ingested successfully',
            'article': article.to_dict(),
            'used_html': bool(html_content),
            'downloaded_images': downloaded_images_count
        }), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@bp.route('/ingest/browser_clipper', methods=['POST'])
def ingest_from_browser_clipper():
    """
    从浏览器插件剪藏内容
    
    Request Body:
    {
        "type": "article" | "note",
        "title": "文章标题",
        "url": "原文链接",
        "author": "作者",
        "published_date": "发布日期",
        "content": "HTML 内容",
        "text_content": "纯文本内容",
        "description": "摘要",
        "images": [图片列表],
        "tags": [标签列表],
        "source": "browser_clipper"
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        content_type = data.get('type', 'article')
        title = data.get('title', '').strip()
        url = data.get('url', '')
        
        if not title:
            return jsonify({'error': 'Title is required'}), 400
        
        session = get_session()
        Paper, Note, Article = get_models()
        
        # 检查是否已存在（基于 URL）
        if url:
            existing_article = session.query(Article).filter(
                Article.url == url
            ).first()
            
            if existing_article:
                return jsonify({
                    'message': 'Article already exists',
                    'article': existing_article.to_dict(),
                    'duplicate': True
                }), 200
        
        if content_type == 'note':
            # 保存到笔记库
            note_id = str(uuid.uuid4())[:8]
            content_md = data.get('content', '')
            
            # 保存 Markdown 文件
            try:
                from backend.config import BASE_DIR
            except ImportError:
                from config import BASE_DIR
            notes_dir = BASE_DIR / 'data/papers/notes'
            notes_dir.mkdir(parents=True, exist_ok=True)
            
            md_file = notes_dir / f'note_{note_id}.md'
            md_file.write_text(content_md, encoding='utf-8')
            
            # 创建笔记记录
            note = Note(
                id=note_id,
                title=title,
                content=content_md,
                source=data.get('source', 'browser_clipper'),
                source_url=url
            )
            
            session.add(note)
            session.flush()
            
            # 添加标签
            tags = data.get('tags', [])
            if tags:
                from backend.models import Tag
                for tag_name in tags:
                    tag = session.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                        session.flush()
                    note.tags.append(tag)
            
            session.commit()
            session.refresh(note)
            
            return jsonify({
                'message': 'Note saved successfully',
                'note': note.to_dict(),
                'type': 'note'
            }), 201
        
        else:
            # 保存到文章库
            html_content = data.get('content', '')
            text_content = data.get('text_content', '')
            
            # 生成唯一 ID
            article_id = str(uuid.uuid4())[:8]
            
            # 保存 HTML 文件
            try:
                from backend.config import BASE_DIR
            except ImportError:
                from config import BASE_DIR
            web_dir = BASE_DIR / 'data/papers/web'
            web_dir.mkdir(parents=True, exist_ok=True)
            
            safe_url = url.replace('://', '_').replace('/', '_') if url else article_id
            html_file = web_dir / f'{article_id}_{safe_url}.html'
            html_file.write_text(html_content, encoding='utf-8')
            
            # 下载图片
            images = data.get('images', [])
            downloaded_images = []
            
            if images:
                images_dir = web_dir / f'{article_id}_{safe_url}_files'
                images_dir.mkdir(exist_ok=True)
                
                import requests as req_lib
                for img in images[:10]:  # 最多下载10张
                    try:
                        img_url = img.get('src', '')
                        if not img_url.startswith(('http://', 'https://')):
                            continue
                        
                        img_response = req_lib.get(img_url, timeout=10)
                        if img_response.status_code == 200:
                            img_filename = uuid.uuid4().hex + '.jpg'
                            img_path = images_dir / img_filename
                            img_path.write_bytes(img_response.content)
                            downloaded_images.append(str(img_path))
                    except Exception as e:
                        print(f'Failed to download image: {e}')
            
            # 创建文章记录
            # 处理发布日期（转换为 date 对象）
            published_date = None
            pub_date_str = data.get('published_date')
            if pub_date_str:
                try:
                    from datetime import datetime as dt
                    # 尝试解析 ISO 格式
                    if 'T' in pub_date_str:
                        published_date = dt.fromisoformat(pub_date_str.replace('Z', '+00:00')).date()
                    else:
                        published_date = dt.strptime(pub_date_str, '%Y-%m-%d').date()
                except Exception:
                    published_date = None
            
            article = Article(
                title=title,
                url=url,
                author=data.get('author', ''),
                published_at=published_date,
                content=data.get('description', ''),
                file_path=str(html_file),
                source='web',
                status='unread',
                starred=False
            )
            
            session.add(article)
            session.flush()
            
            # 添加标签
            tags = data.get('tags', [])
            if tags:
                from backend.models import Tag
                for tag_name in tags:
                    tag = session.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name)
                        session.add(tag)
                        session.flush()
                    article.tags.append(tag)
            
            session.commit()
            session.refresh(article)
            
            return jsonify({
                'message': 'Article saved successfully',
                'article': article.to_dict(),
                'type': 'article',
                'downloaded_images': len(downloaded_images)
            }), 201
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500
