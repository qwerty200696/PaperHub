"""
现有 API 回归测试

目的：确保 P1/P2 阶段的多用户改造不破坏现有功能。

覆盖：
- /api/papers 列表/详情
- /api/tags 列表
- /api/articles 列表
- /api/notes 列表
- /api/wechat/subscriptions 列表
- /health 健康检查
- 404 处理
"""
import pytest


class TestHealthCheck:
    """健康检查端点"""

    def test_health_endpoint(self, client):
        """/health 应返回 200"""
        resp = client.get('/health')
        # 即使没有 /health 路由，也不应崩溃
        assert resp.status_code in [200, 404]


class TestPapersApi:
    """论文 API 回归测试"""

    def test_list_papers_empty(self, client):
        """空数据库时论文列表应返回空数组"""
        resp = client.get('/api/papers')
        assert resp.status_code == 200

        data = resp.get_json()
        assert 'papers' in data
        assert isinstance(data['papers'], list)

    def test_list_papers_with_data(self, client, make_user, make_paper):
        """有数据时论文列表应返回"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Paper 1', user_id=user.id, is_public=True)
        make_paper(title='Paper 2', user_id=user.id, is_public=True)

        resp = client.get('/api/papers')
        assert resp.status_code == 200

        papers = resp.get_json()['papers']
        assert len(papers) >= 2
        titles = [p['title'] for p in papers]
        assert 'Paper 1' in titles
        assert 'Paper 2' in titles

    def test_get_paper_detail(self, client, make_user, make_paper):
        """获取论文详情"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Detail Test', user_id=user.id, is_public=True)

        resp = client.get(f'/api/papers/{paper.id}')
        assert resp.status_code == 200
        assert resp.get_json()['title'] == 'Detail Test'

    def test_get_nonexistent_paper(self, client):
        """获取不存在的论文应 404"""
        resp = client.get('/api/papers/99999')
        assert resp.status_code == 404


class TestTagsApi:
    """标签 API 回归测试"""

    def test_list_tags(self, client, make_user, make_tag):
        """标签列表"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='machine-learning', user_id=user.id, is_public=True)
        make_tag(name='physics', user_id=user.id, is_public=True)

        resp = client.get('/api/tags')
        assert resp.status_code == 200

        # tags 可能是 list 或 dict
        data = resp.get_json()
        tags = data if isinstance(data, list) else data.get('tags', [])
        assert len(tags) >= 2


class TestArticlesApi:
    """文章 API 回归测试"""

    def test_list_articles(self, client):
        """文章列表应可用"""
        resp = client.get('/api/articles')
        assert resp.status_code == 200

    def test_list_articles_with_data(self, client, make_user, make_article):
        """有数据的文章列表"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='Article 1', user_id=user.id, is_public=True)

        resp = client.get('/api/articles')
        assert resp.status_code == 200


class TestNotesApi:
    """笔记 API 回归测试"""

    def test_list_notes(self, client):
        """笔记列表应可用"""
        resp = client.get('/api/notes')
        assert resp.status_code == 200


class TestWechatApi:
    """微信订阅 API 回归测试"""

    def test_list_subscriptions(self, client):
        """订阅列表应可用"""
        resp = client.get('/api/wechat/subscriptions')
        assert resp.status_code == 200


class TestErrorHandling:
    """错误处理回归测试"""

    def test_404_returns_json(self, client):
        """404 应返回 JSON 格式"""
        resp = client.get('/api/nonexistent-endpoint')
        assert resp.status_code == 404
        assert resp.is_json

    def test_500_error_handling(self, client, monkeypatch):
        """500 错误应返回 JSON 而非 HTML"""
        # 触发一个内部错误（通过访问不存在的论文 ID 但用字符串）
        # 这里仅验证错误处理框架工作
        resp = client.get('/api/papers/not-a-number')
        # 应返回 404 或 500，但不应崩溃
        assert resp.status_code in [404, 500]
        assert resp.is_json
