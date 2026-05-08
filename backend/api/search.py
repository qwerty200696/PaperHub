"""搜索 API 端点"""

from flask import Blueprint, request, jsonify
from services.search_service import (
    search_papers,
    search_articles,
    search_notes,
    search_all,
    get_search_suggestions
)

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
def search():
    """全文搜索接口"""
    try:
        query = request.args.get('q', '')
        module = request.args.get('module', 'all')
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        highlight = request.args.get('highlight', 'true').lower() == 'true'
        
        if not query.strip():
            return jsonify({
                'success': False,
                'error': '请输入搜索关键词'
            }), 400
        
        if module == 'papers':
            result = search_papers(query, page, size, highlight)
        elif module == 'articles':
            result = search_articles(query, page, size, highlight)
        elif module == 'notes':
            result = search_notes(query, page, size, highlight)
        else:
            result = search_all(query, page, size, highlight)
        
        return jsonify({
            'success': True,
            'total': result['total'],
            'page': page,
            'size': size,
            'results': result['results'],
            'breakdown': result.get('breakdown', None)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@search_bp.route('/search/suggest', methods=['GET'])
def suggest():
    """搜索建议接口"""
    try:
        query = request.args.get('q', '')
        limit = int(request.args.get('limit', 5))
        
        suggestions = get_search_suggestions(query, limit)
        
        return jsonify({
            'success': True,
            'suggestions': suggestions
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500