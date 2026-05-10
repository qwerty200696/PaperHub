"""
PaperHub Backend - Flask 主应用
"""
from flask import Flask, jsonify, send_from_directory, request
from pathlib import Path
from flask_cors import CORS
import logging

try:
    from backend.config import config, BASE_DIR, init_db, get_session, close_scoped_session
except ImportError:
    from config import config, BASE_DIR, init_db, get_session, close_scoped_session


_scan_patterns = [
    '/sse', '/status', '/v1/mcp', '/api/mcp', '/mcp',
    '/soap/', '/cgi-bin/', '/_catalog', '/web-static/',
    '/favicon.ico/', '/favicon.png', '/.env', '/.git',
    '/wp-', '/phpmyadmin', '/admin', '/manager',
    '/api/v1/', '/api/v2/', '/actuator', '/swagger',
    '/.well-known/', '/apple-app-site-association'
]


def _is_scan_request(path):
    for pattern in _scan_patterns:
        if pattern in path:
            return True
    return False


class ScanFilter(logging.Filter):
    def filter(self, record):
        msg = record.getMessage()
        for pattern in _scan_patterns:
            if pattern in msg:
                return False
        return True


def create_app(config_name='default'):
    app = Flask(__name__, static_folder=str(BASE_DIR / 'frontend'))
    app.config.from_object(config[config_name])
    app.config['JSON_AS_ASCII'] = False

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    werkzeug_logger = logging.getLogger('werkzeug')
    werkzeug_logger.addFilter(ScanFilter())

    CORS(app, origins=app.config['CORS_ORIGINS'])

    init_db()

    register_routes(app)

    @app.errorhandler(Exception)
    def handle_exception(e):
        import traceback
        from werkzeug.exceptions import HTTPException, NotFound
        path = request.path
        if isinstance(e, NotFound) and _is_scan_request(path):
            return jsonify({
                'error': 'Not Found',
                'type': 'NotFound'
            }), 404
        app.logger.error(f"未处理的异常: {e}\n{traceback.format_exc()}")
        if isinstance(e, HTTPException):
            return jsonify({
                'error': str(e),
                'type': type(e).__name__
            }), e.code
        return jsonify({
            'error': str(e),
            'type': type(e).__name__
        }), 500

    init_database()

    @app.route('/')
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/modular')
    def modular():
        return send_from_directory(app.static_folder, 'index_modular.html')

    @app.route('/health')
    def health():
        return jsonify({'status': 'ok'})

    @app.route('/favicon.ico')
    def favicon():
        return '', 204

    @app.route('/static/wechat/<path:filename>')
    def wechat_static(filename):
        return send_from_directory(str(BASE_DIR / 'data/papers/wechat'), filename)

    @app.route('/static/zhihu/<path:filename>')
    def zhihu_static(filename):
        return send_from_directory(str(BASE_DIR / 'data/papers/zhihu'), filename)

    @app.route('/static/note_images/<path:filename>')
    def note_images_static(filename):
        return send_from_directory(str(BASE_DIR / 'data/papers/note_images'), filename)

    @app.route('/src/<path:filename>')
    def frontend_src(filename):
        return send_from_directory(str(BASE_DIR / 'frontend/src'), filename)

    @app.teardown_appcontext
    def shutdown_session(exception=None):
        close_scoped_session(exception)

    return app


def register_routes(app):
    try:
        from backend.api import papers, ingest, notes, articles, ai, wechat_subscription, search, note_images, web_extract
    except ImportError:
        from api import papers, ingest, notes, articles, ai, wechat_subscription, search, note_images, web_extract

    app.register_blueprint(papers.bp, url_prefix='/api')
    app.register_blueprint(ingest.bp, url_prefix='/api')
    app.register_blueprint(wechat_subscription.bp, url_prefix='/api')
    app.register_blueprint(search.search_bp, url_prefix='/api')
    app.register_blueprint(ai.bp)
    app.register_blueprint(note_images.bp)
    app.register_blueprint(web_extract.bp, url_prefix='/api')
    notes.get_note_routes(app)
    articles.get_article_routes(app)


def init_database():
    try:
        from backend.models import Base, Tag, Paper
    except ImportError:
        from models import Base, Tag, Paper

    try:
        from backend.config import get_engine
    except ImportError:
        from config import get_engine
    engine = get_engine()
    Base.metadata.create_all(engine)

    session = get_session()

    if session.query(Tag).first():
        Base.metadata.create_all(get_engine())
        try:
            has_notes_to_migrate = session.query(Paper).filter(Paper.source == 'note').count()
            if has_notes_to_migrate > 0:
                print(f'⚠️ 发现 {has_notes_to_migrate} 条待迁移笔记，请手动运行 python backend/services/migrate_notes.py')
        except Exception as e:
            pass
        session.close()
        return

    tech_tags = [
        ('Transformer', 'tech', '#409EFF'),
        ('Diffusion', 'tech', '#67C23A'),
        ('YOLO', 'tech', '#E6A23C'),
        ('RAG', 'tech', '#F56C6C'),
        ('LoRA', 'tech', '#909399'),
        ('LLM', 'tech', '#00CED1'),
        ('CNN', 'tech', '#9370DB'),
        ('ViT', 'tech', '#FF6347'),
    ]

    conf_tags = [
        ('CVPR2024', 'conference', '#409EFF'),
        ('ICCV2023', 'conference', '#67C23A'),
        ('NeurIPS2024', 'conference', '#E6A23C'),
        ('ICML2024', 'conference', '#F56C6C'),
        ('arXiv', 'conference', '#909399'),
    ]

    custom_tags = [
        ('必读', 'custom', '#F56C6C'),
        ('待复现', 'custom', '#E6A23C'),
        ('落地可用', 'custom', '#67C23A'),
        ('冷门但有启发', 'custom', '#909399'),
    ]

    for name, tag_type, color in tech_tags + conf_tags + custom_tags:
        tag = Tag(name=name, type=tag_type, color=color)
        session.add(tag)

    session.commit()
    session.close()


if __name__ == '__main__':
    import sys
    port = 5799
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port = int(sys.argv[1])

    app = create_app('development')
    print(f"""
╔════════════════════════════════════════╗
║     PaperHub - Backend Server          ║
║     http://localhost:{port:<5d}              ║
╚════════════════════════════════════════╝
    """)
    app.run(host='0.0.0.0', port=port, debug=True)
