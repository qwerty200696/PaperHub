from flask import Blueprint, request, jsonify
from pathlib import Path
import logging

try:
    from backend.config import BASE_DIR
    from backend.services.web_parser import UniversalWebParser
except ImportError:
    from config import BASE_DIR
    from services.web_parser import UniversalWebParser

logger = logging.getLogger(__name__)
bp = Blueprint('web_extract', __name__)

web_parser = UniversalWebParser()


@bp.route('/web/extract', methods=['POST'])
def extract_web_content():
    data = request.get_json() or {}
    url = data.get('url', '')
    method = data.get('method', 'auto')
    
    if not url:
        return jsonify({'error': 'url不能为空'}), 400
    
    try:
        result = web_parser.extract_article(url, preferred_method=method)
        return jsonify(result)
    except Exception as e:
        logger.error(f"网页提取API错误: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/web/save-page', methods=['POST'])
def save_complete_web_page():
    data = request.get_json() or {}
    url = data.get('url', '')
    
    if not url:
        return jsonify({'error': 'url不能为空'}), 400
    
    try:
        save_dir = BASE_DIR / 'data' / 'saved_web_pages'
        result = web_parser.save_complete_page(url, save_dir)
        return jsonify(result)
    except Exception as e:
        logger.error(f"保存网页API错误: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/web/test', methods=['GET'])
def web_test():
    return jsonify({
        'message': 'Web Extraction API is running!',
        'endpoints': {
            '/api/web/extract': 'POST - 提取网页正文，参数: url, method(可选)',
            '/api/web/save-page': 'POST - 保存完整网页，参数: url'
        }
    })
