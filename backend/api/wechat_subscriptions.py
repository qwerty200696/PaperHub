"""
精选公众号 API
从TXT文件读取公众号文章列表
"""
import json
from pathlib import Path
from flask import Blueprint, request, jsonify
from datetime import datetime

bp = Blueprint('wechat_subscriptions', __name__, url_prefix='/api/wechat-subscriptions')


def parse_publish_time(time_str):
    """解析发布时间字符串，支持多种格式"""
    if not time_str:
        return datetime.min
    formats = [
        '%Y-%m-%dT%H:%M:%S',
        '%Y-%m-%d %H:%M:%S',
        '%Y-%m-%dT%H:%M:%S.%f',
        '%Y-%m-%d %H:%M',
        '%Y-%m-%d',
    ]
    for fmt in formats:
        try:
            return datetime.strptime(time_str, fmt)
        except ValueError:
            continue
    return datetime.min


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


@bp.route('/backup', methods=['POST'])
def backup_article():
    """
    备份文章到精选公众号TXT文件
    POST /api/wechat-subscriptions/backup
    Body: { "subscription_name": "宝玉AI", "article": { "title": "...", "url": "...", ... } }
    """
    data = request.get_json()
    if not data:
        return jsonify({'error': '请求体不能为空'}), 400

    subscription_name = data.get('subscription_name', '').strip()
    article = data.get('article')

    if not subscription_name:
        return jsonify({'error': 'subscription_name 不能为空'}), 400
    if not article or not isinstance(article, dict):
        return jsonify({'error': 'article 不能为空且必须为对象'}), 400
    if not article.get('title') or not article.get('url'):
        return jsonify({'error': 'article 必须包含 title 和 url'}), 400

    txt_file = get_subscription_file(subscription_name)
    subs_dir = get_subscriptions_dir()
    subs_dir.mkdir(parents=True, exist_ok=True)

    # 读取现有内容
    existing_lines = []
    existing_urls = set()
    if txt_file.exists():
        with open(txt_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    existing_lines.append(line)
                    try:
                        existing_article = json.loads(line)
                        existing_urls.add(existing_article.get('url', ''))
                    except json.JSONDecodeError:
                        pass

    article_url = article.get('url', '')
    if article_url in existing_urls:
        return jsonify({
            'message': '文章已存在，跳过备份',
            'subscription_name': subscription_name,
            'skipped': True
        }), 200

    # 确保文章数据包含必要字段
    article_to_save = {
        'publish_time': article.get('publish_time') or article.get('published_at', ''),
        'id': article.get('id', ''),
        'title': article.get('title', ''),
        'url': article.get('url', ''),
        'summary': article.get('summary') or article.get('digest', ''),
        'cover': article.get('cover', '')
    }

    # 将所有文章（现有+新增）解析后按发布时间倒序排列
    all_articles = [article_to_save]
    for line in existing_lines:
        try:
            all_articles.append(json.loads(line))
        except json.JSONDecodeError:
            continue

    # 按发布时间倒序排列（最新的在最前面）
    all_articles.sort(
        key=lambda a: parse_publish_time(a.get('publish_time', '')),
        reverse=True
    )

    with open(txt_file, 'w', encoding='utf-8') as f:
        for article_data in all_articles:
            f.write(json.dumps(article_data, ensure_ascii=False) + '\n')

    return jsonify({
        'message': '备份成功',
        'subscription_name': subscription_name,
        'article_count': len(updated_lines),
        'skipped': False
    }), 200


def get_subscription_routes(app):
    """注册路由"""
    app.register_blueprint(bp)
