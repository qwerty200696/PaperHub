"""
精选公众号 API
从TXT文件读取公众号文章列表
"""
import json
from pathlib import Path
from flask import Blueprint, request, jsonify

bp = Blueprint('wechat_subscriptions', __name__, url_prefix='/api/wechat-subscriptions')


def get_subscriptions_dir():
    """获取公众号订阅数据目录"""
    try:
        from backend.config import PAPERS_DIR
        return PAPERS_DIR / 'wechat_subscriptions'
    except ImportError:
        from config import PAPERS_DIR
        return PAPERS_DIR / 'wechat_subscriptions'


def get_subscription_file(subscription_name: str) -> Path:
    """获取指定公众号的TXT文件路径"""
    subs_dir = get_subscriptions_dir()
    return subs_dir / f'{subscription_name}.txt'


@bp.route('/list', methods=['GET'])
def list_subscriptions():
    """获取所有可用的公众号订阅列表"""
    subs_dir = get_subscriptions_dir()

    if not subs_dir.exists():
        return jsonify({'subscriptions': [], 'total': 0})

    subscriptions = []
    for txt_file in subs_dir.glob('*.txt'):
        name = txt_file.stem
        with open(txt_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        subscriptions.append({
            'name': name,
            'article_count': len(lines)
        })

    return jsonify({
        'subscriptions': subscriptions,
        'total': len(subscriptions)
    }), 200


@bp.route('/articles', methods=['GET'])
def get_articles():
    """
    获取指定公众号的文章列表
    GET /api/wechat-subscriptions/articles?name=宝玉AI&offset=0&limit=100
    """
    subscription_name = request.args.get('name', '')
    if not subscription_name:
        return jsonify({'error': 'name parameter is required'}), 400

    offset = request.args.get('offset', 0, type=int)
    limit = request.args.get('limit', 100, type=int)

    txt_file = get_subscription_file(subscription_name)
    if not txt_file.exists():
        return jsonify({'error': f'Subscription "{subscription_name}" not found'}), 404

    with open(txt_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    total = len(lines)

    articles = []
    for line in lines[offset:offset + limit]:
        line = line.strip()
        if line:
            try:
                article = json.loads(line)
                articles.append(article)
            except json.JSONDecodeError:
                continue

    return jsonify({
        'subscription': subscription_name,
        'articles': articles,
        'total': total,
        'offset': offset,
        'limit': limit,
        'has_more': offset + limit < total
    }), 200


def get_subscription_routes(app):
    """注册路由"""
    app.register_blueprint(bp)
