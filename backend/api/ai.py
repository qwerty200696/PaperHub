"""
AI API - 大模型相关 API
"""
import json
from flask import Blueprint, jsonify, request

bp = Blueprint('ai', __name__)


def get_llm_client():
    try:
        from backend.services.llm_client import get_llm_client as _get_client
    except ImportError:
        from services.llm_client import get_llm_client as _get_client
    return _get_client()


def get_prompt_engine():
    try:
        from backend.services.prompt_engine import PromptEngine
    except ImportError:
        from services.prompt_engine import PromptEngine
    return PromptEngine


def get_session():
    try:
        from backend.config import get_session as _get_session
    except ImportError:
        from config import get_session as _get_session
    return _get_session()


def get_models():
    try:
        from backend.models import Paper, Tag, Article, Note
    except ImportError:
        from models import Paper, Tag, Article, Note
    return Paper, Tag, Article, Note


@bp.route('/api/ai/config', methods=['POST'])
def configure_ai():
    data = request.get_json()
    provider = data.get('provider', 'doubao')
    api_key = data.get('api_key', '')
    base_url = data.get('base_url', '')
    model_id = data.get('model_id', '')
    temperature = data.get('temperature', 0)

    if not api_key:
        return jsonify({'error': 'API key is required'}), 400

    client = get_llm_client()
    client.configure(provider=provider, api_key=api_key, base_url=base_url, model_id=model_id, temperature=temperature)

    return jsonify({'message': 'AI configured successfully', 'provider': provider})


@bp.route('/api/ai/config', methods=['GET'])
def get_ai_config():
    client = get_llm_client()
    return jsonify({
        'provider': client.provider,
        'has_api_key': bool(client.api_key),
        'api_key': client.api_key or '',
        'base_url': client.base_url or '',
        'model_id': getattr(client, 'model_id', '') or '',
        'temperature': getattr(client, 'temperature', 0)
    })


@bp.route('/api/ai/stats', methods=['GET'])
def get_usage_stats():
    client = get_llm_client()
    return jsonify(client.get_usage())


@bp.route('/api/ai/summary', methods=['POST'])
def generate_summary():
    data = request.get_json()
    paper_id = data.get('paper_id')
    content_source = data.get('source', 'paper')
    title = data.get('title', '')
    abstract = data.get('abstract', '')
    content = data.get('content', '')

    if not paper_id and not title:
        return jsonify({'error': 'paper_id or title is required'}), 400

    if paper_id:
        Paper, _, _, _ = get_models()
        session = get_session()
        try:
            if content_source == 'article':
                item = session.query(Article).filter(Article.id == paper_id, Article.is_deleted == False).first()
            elif content_source == 'note':
                item = session.query(Note).filter(Note.id == paper_id, Note.is_deleted == False).first()
            else:
                item = session.query(Paper).filter(Paper.id == paper_id).first()

            if not item:
                return jsonify({'error': 'Content not found'}), 404

            title = item.title
            abstract = getattr(item, 'abstract', '') or ''
            content = getattr(item, 'content', '') or ''
        finally:
            session.close()

    PromptEngine = get_prompt_engine()
    client = get_llm_client()

    if not client.api_key:
        return jsonify({'error': 'API key not configured. Please set your API key in settings.'}), 400

    messages = PromptEngine.build(
        'paper_summary',
        title=title,
        abstract=abstract or '无',
        content=content[:3000] if content else '无正文内容'
    )

    try:
        result = client.chat_completion(messages, temperature=0.0)
    except Exception as e:
        print(f"DEBUG - AI Summary Error: {str(e)}")
        import traceback
        print(f"DEBUG - Traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

    if result.get('error'):
        return jsonify({'error': result['error']}), 500

    return jsonify({
        'summary': result['content'],
        'model': result.get('model', 'unknown'),
        'provider': result.get('provider', 'unknown')
    })


@bp.route('/api/ai/recommend-tags', methods=['POST'])
def recommend_tags():
    data = request.get_json()
    paper_id = data.get('paper_id')
    content_source = data.get('source', 'paper')
    title = data.get('title', '')
    abstract = data.get('abstract', '')
    content = data.get('content', '')

    if not paper_id and not title:
        return jsonify({'error': 'paper_id or title is required'}), 400

    if paper_id:
        Paper, Tag, Article, _ = get_models()
        session = get_session()
        try:
            if content_source == 'article':
                item = session.query(Article).filter(Article.id == paper_id, Article.is_deleted == False).first()
            else:
                item = session.query(Paper).filter(Paper.id == paper_id).first()

            if not item:
                return jsonify({'error': 'Content not found'}), 404

            title = item.title
            abstract = getattr(item, 'abstract', '') or ''
            content = getattr(item, 'content', '') or ''

            all_tags = session.query(Tag).all()
            existing_tags = [t.name for t in all_tags]
        finally:
            session.close()
    else:
        existing_tags = data.get('existing_tags', [])

    PromptEngine = get_prompt_engine()
    client = get_llm_client()

    if not client.api_key:
        return jsonify({'error': 'API key not configured. Please set your API key in settings.'}), 400

    messages = PromptEngine.build(
        'auto_tag',
        existing_tags=', '.join(existing_tags) if existing_tags else '暂无标签',
        title=title,
        abstract=abstract or '无',
        content_preview=content[:2000] if content else '无正文内容'
    )

    result = client.chat_completion(messages, temperature=0.0)

    if result.get('error'):
        return jsonify({'error': result['error']}), 500

    try:
        import re
        json_match = re.search(r'\{[^{}]*\}', result['content'], re.DOTALL)
        if json_match:
            tag_data = json.loads(json_match.group())
        else:
            tag_data = json.loads(result['content'])
    except json.JSONDecodeError:
        return jsonify({
            'recommended_tags': [],
            'new_tags': [],
            'reason': '解析失败，请重试'
        })

    return jsonify(tag_data)


@bp.route('/api/ai/related', methods=['POST'])
def find_related():
    data = request.get_json()
    current_id = data.get('current_id')
    current_title = data.get('title', '')
    current_abstract = data.get('abstract', '')
    candidate_ids = data.get('candidate_ids', [])

    if not current_title and not current_id:
        return jsonify({'error': 'current_id or title is required'}), 400

    if not candidate_ids:
        return jsonify({'related': []})

    Paper, _, Article, _ = get_models()
    session = get_session()
    try:
        candidates = []
        for cid in candidate_ids[:5]:
            paper = session.query(Paper).filter(Paper.id == cid).first()
            if paper:
                candidates.append({
                    'id': paper.id,
                    'title': paper.title,
                    'abstract': paper.abstract or '',
                    'type': 'paper'
                })

        if not candidates:
            return jsonify({'related': []})

        PromptEngine = get_prompt_engine()
        client = get_llm_client()

        if not client.api_key:
            return jsonify({'error': 'API key not configured'}), 400

        candidates_text = '\n'.join([
            f"[{i+1}] {c['title']} - {c['abstract'][:200]}"
            for i, c in enumerate(candidates)
        ])

        messages = PromptEngine.build(
            'related_content',
            current_title=current_title,
            current_abstract=current_abstract or '无',
            candidates=candidates_text
        )

        result = client.chat_completion(messages, temperature=0.0)

        if result.get('error'):
            return jsonify({'error': result['error']}), 500

        try:
            related = json.loads(result['content'])
        except json.JSONDecodeError:
            related = []
            for i, c in enumerate(candidates[:3]):
                related.append({
                    'id': c['id'],
                    'title': c['title'],
                    'relevance_score': 70,
                    'reason': '基于内容相似度推荐'
                })

        return jsonify({'related': related})
    finally:
        session.close()


@bp.route('/api/ai/clear-cache', methods=['POST'])
def clear_cache():
    client = get_llm_client()
    client.clear_cache()
    return jsonify({'message': 'Cache cleared'})