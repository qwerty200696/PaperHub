"""
微信公众号订阅 API
"""
from datetime import datetime, timedelta
from flask import Blueprint, jsonify, request
import requests
import re

bp = Blueprint('wechat_subscription', __name__)

USER_AGENT = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'

DEFAULT_API_KEY = '1ec4c9852ff34f74aac7bd436346af6b'


def search_wechat_account(keyword, begin=0, size=5, api_key=None):
    """搜索微信公众号"""
    url = 'https://down.mptext.top/api/public/v1/account'
    
    params = {
        'keyword': keyword,
        'begin': begin,
        'size': size
    }
    
    headers = {
        'X-Auth-Key': api_key or DEFAULT_API_KEY,
        'User-Agent': USER_AGENT
    }
    
    try:
        response = requests.get(url, params=params, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json()
            if data.get('base_resp', {}).get('ret') == 0:
                return data.get('list', []), None
            else:
                return [], data.get('err_msg', 'Unknown error')
    except Exception as e:
        print(f'搜索公众号失败: {e}')
        return [], str(e)
    
    return [], None


def fetch_wechat_articles(account_id, count=10, api_key=None, offset=0):
    """爬取微信公众号文章列表（使用第三方API）
    
    Args:
        account_id: 公众号fakeid，如 MzA3MzI4MjgzMw==
        count: 获取文章数量
        api_key: 第三方API密钥
        offset: 起始偏移量
    
    Returns:
        list: 文章列表，包含title, url, published_at等字段
        error: 错误信息（如有）
    """
    articles = []
    url = 'https://down.mptext.top/api/public/v1/article'
    headers = {
        'X-Auth-Key': api_key or DEFAULT_API_KEY,
        'User-Agent': USER_AGENT
    }
    
    if not account_id:
        return articles, None
    
    remaining = count
    begin = offset
    max_per_request = 20
    
    while remaining > 0:
        size = min(remaining, max_per_request)
        
        params = {
            'fakeid': account_id,
            'begin': begin,
            'size': size
        }
        
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if data.get('base_resp', {}).get('ret') == 0:
                    new_articles = data.get('articles', [])
                    if not new_articles:
                        break
                    
                    for article in new_articles:
                        publish_time = article.get('update_time', 0)
                        published_at = datetime.fromtimestamp(publish_time) if publish_time else datetime.now()
                        articles.append({
                            'title': article.get('title', ''),
                            'url': article.get('link', ''),
                            'published_at': published_at,
                            'digest': article.get('digest', ''),
                            'cover': article.get('cover', '')
                        })
                    
                    remaining -= len(new_articles)
                    begin += len(new_articles)
                    
                    if len(new_articles) < size:
                        break
                else:
                    return articles, f"API返回错误: {data.get('base_resp', {}).get('err_msg', '未知错误')}"
            else:
                return articles, f"HTTP错误: {response.status_code}"
        except Exception as e:
            if articles:
                return articles, f"部分成功，获取了 {len(articles)} 篇文章，最后错误: {str(e)}"
            return articles, str(e)
    
    return articles, None


def get_session():
    try:
        from backend.config import get_session as _get_session
    except ImportError:
        from config import get_session as _get_session
    return _get_session()


def get_models():
    try:
        from backend.models import WechatSubscription, Article
    except ImportError:
        from models import WechatSubscription, Article
    return WechatSubscription, Article


@bp.route('/wechat/subscriptions', methods=['GET'])
def get_subscriptions():
    """获取所有订阅的微信公众号"""
    WechatSubscription, Article = get_models()
    session = get_session()
    
    subscriptions = session.query(WechatSubscription).order_by(WechatSubscription.created_at.desc()).all()
    result = [sub.to_dict() for sub in subscriptions]
    
    session.close()
    return jsonify(result)


@bp.route('/wechat/search_account', methods=['GET'])
def search_account():
    """搜索微信公众号（使用第三方API）"""
    keyword = request.args.get('keyword')
    if not keyword:
        return jsonify({'error': '缺少 keyword 参数'}), 400
    
    begin = int(request.args.get('begin', 0))
    size = int(request.args.get('size', 5))
    api_key = request.args.get('api_key')
    
    accounts, error = search_wechat_account(keyword, begin, size, api_key)
    
    result = []
    for account in accounts:
        result.append({
            'name': account.get('nickname', ''),
            'id': account.get('fakeid', ''),
            'alias': account.get('alias', ''),
            'desc': account.get('signature', ''),
            'avatar': account.get('round_head_img', '')
        })
    
    if error:
        return jsonify({
            'message': '搜索失败',
            'error': error,
            'accounts': result
        }), 500
    
    return jsonify({
        'message': '搜索成功',
        'accounts': result
    })


def get_wechat_config_model():
    """获取 WechatConfig 模型"""
    try:
        from backend.models import WechatConfig
    except ImportError:
        from models import WechatConfig
    return WechatConfig


@bp.route('/wechat/config', methods=['GET'])
def get_wechat_config():
    """获取微信公众号相关配置"""
    WechatConfig = get_wechat_config_model()
    
    session = get_session()
    config = session.query(WechatConfig).first()
    
    api_key = config.api_key if config and config.api_key else DEFAULT_API_KEY
    session.close()
    
    return jsonify({
        'api_key': api_key,
        'has_custom_key': config and config.api_key is not None
    })


@bp.route('/wechat/config', methods=['POST'])
def save_wechat_config():
    """保存微信公众号配置"""
    data = request.get_json()
    api_key = data.get('api_key', '').strip()
    
    WechatConfig = get_wechat_config_model()
    session = get_session()
    
    config = session.query(WechatConfig).first()
    if config:
        config.api_key = api_key if api_key else None
    else:
        config = WechatConfig(api_key=api_key if api_key else None)
        session.add(config)
    
    session.commit()
    session.close()
    
    return jsonify({
        'message': '配置保存成功',
        'api_key': api_key or DEFAULT_API_KEY
    })


@bp.route('/wechat/subscriptions', methods=['POST'])
def add_subscription():
    """添加微信公众号订阅"""
    data = request.get_json()
    if not data or 'account_name' not in data:
        return jsonify({'error': '缺少 account_name 参数'}), 400
    
    WechatSubscription, Article = get_models()
    session = get_session()
    
    account_name = data['account_name'].strip()
    account_id = data.get('account_id')
    if account_id:
        account_id = account_id.strip()
    
    existing = session.query(WechatSubscription).filter(
        WechatSubscription.account_name == account_name
    ).first()
    if existing:
        session.close()
        return jsonify({'error': '该公众号已订阅'}), 409
    
    subscription = WechatSubscription(
        account_name=account_name,
        account_id=account_id if account_id else None
    )
    
    session.add(subscription)
    session.commit()
    session.refresh(subscription)
    
    session.close()
    return jsonify({
        'message': '订阅成功',
        'subscription': subscription.to_dict()
    }), 201


@bp.route('/wechat/subscriptions/<int:subscription_id>', methods=['DELETE'])
def delete_subscription(subscription_id):
    """删除微信公众号订阅"""
    WechatSubscription, Article = get_models()
    session = get_session()
    
    subscription = session.query(WechatSubscription).get(subscription_id)
    if not subscription:
        session.close()
        return jsonify({'error': '订阅不存在'}), 404
    
    session.delete(subscription)
    session.commit()
    session.close()
    
    return jsonify({'message': '取消订阅成功'}), 200


@bp.route('/wechat/subscriptions/check', methods=['POST'])
def check_new_articles():
    """检查订阅的公众号是否有新文章（使用第三方API）"""
    data = request.get_json()
    subscription_ids = data.get('subscription_ids', [])
    api_key = data.get('api_key')
    offset = data.get('offset', 0)
    size = data.get('size', 5)
    
    WechatSubscription, Article = get_models()
    session = get_session()
    
    if subscription_ids:
        subscriptions = session.query(WechatSubscription).filter(
            WechatSubscription.id.in_(subscription_ids)
        ).all()
    else:
        subscriptions = session.query(WechatSubscription).all()
    
    all_crawled_articles = []
    article_urls = set()
    errors = []
    total_available = 0
    
    for sub in subscriptions:
        if not sub.account_id:
            errors.append(f'公众号 "{sub.account_name}" 未设置 account_id')
            continue
        
        crawled_articles, error = fetch_wechat_articles(
            sub.account_id, 
            count=size, 
            api_key=api_key,
            offset=offset
        )
        
        if error:
            errors.append(f'公众号 "{sub.account_name}" 爬取失败: {error}')
            continue
        
        total_available += len(crawled_articles)
        
        for article in crawled_articles:
            if article['url'] not in article_urls:
                article['subscription_name'] = sub.account_name
                article['subscription_id'] = sub.id
                all_crawled_articles.append(article)
                article_urls.add(article['url'])
        
        sub.last_checked_at = datetime.now()
        if crawled_articles:
            latest_published = max([a['published_at'].date() for a in crawled_articles])
            sub.last_post_time = latest_published
    
    all_crawled_articles.sort(key=lambda x: x['published_at'], reverse=True)
    
    # 以API返回的实际数量为准，不做额外分页
    paginated_articles = all_crawled_articles
    total = offset + len(paginated_articles)
    
    new_articles = []
    for article in paginated_articles:
        new_articles.append({
            'id': None,
            'title': article['title'],
            'author': article['subscription_name'],
            'published_at': article['published_at'].isoformat(),
            'url': article['url'],
            'subscription_id': article['subscription_id'],
            'subscription_name': article['subscription_name'],
            'digest': article.get('digest', ''),
            'imported': False
        })
    
    if new_articles:
        urls = [a['url'] for a in new_articles]
        imported_articles = session.query(Article).filter(Article.url.in_(urls), Article.is_deleted == False).all()
        imported_urls = {a.url for a in imported_articles}
        for article in new_articles:
            if article['url'] in imported_urls:
                article['imported'] = True
    
    session.commit()
    session.close()
    
    # 如果API返回的文章数量等于请求的size，说明可能还有更多；否则说明已经到最后了
    has_more = len(all_crawled_articles) >= size
    
    result = {
        'message': f'检查完成，发现 {total} 篇文章',
        'articles': new_articles,
        'total': total,
        'offset': offset,
        'size': size,
        'has_more': has_more
    }
    
    if errors:
        result['errors'] = errors
    
    return jsonify(result)