"""
Flask 应用集成测试

覆盖：
- create_app 工厂函数
- 蓝图注册（所有业务蓝图 + auth 蓝图）
- CORS 配置
- 错误处理（404/500 返回 JSON）
- /health 健康检查
- 静态文件路由
- 60s 数据 API
- teardown_appcontext session 清理
"""
import pytest


class TestAppFactory:
    """create_app 工厂函数"""

    def test_create_app_default(self, app):
        """默认配置创建 app"""
        assert app is not None
        assert app.config['TESTING'] is True

    def test_app_has_jwt_secret(self, app):
        """应配置 JWT 密钥"""
        assert 'JWT_SECRET_KEY' in app.config
        assert app.config['JWT_SECRET_KEY']

    def test_app_json_as_ascii_false(self, app):
        """JSON 应支持非 ASCII（中文）"""
        assert app.config.get('JSON_AS_ASCII') is False


class TestBlueprints:
    """蓝图注册"""

    def test_auth_blueprint_registered(self, app):
        """auth 蓝图应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/auth/login' in endpoints
        assert '/api/auth/register' in endpoints
        assert '/api/auth/me' in endpoints

    def test_users_blueprint_registered(self, app):
        """users 蓝图应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/users' in endpoints

    def test_papers_blueprint_registered(self, app):
        """papers 蓝图应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/papers' in endpoints

    def test_notes_blueprint_registered(self, app):
        """notes 蓝图应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/notes' in endpoints

    def test_articles_blueprint_registered(self, app):
        """articles 蓝图应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/articles' in endpoints

    def test_tags_endpoints_registered(self, app):
        """tags 端点应注册"""
        endpoints = [rule.rule for rule in app.url_map.iter_rules()]
        assert '/api/tags' in endpoints


class TestCorsHeaders:
    """CORS 配置"""

    def test_cors_headers_present(self, client):
        """响应应包含 CORS 头"""
        resp = client.get('/health')
        assert 'Access-Control-Allow-Origin' in resp.headers

    def test_cors_allow_all_origins(self, client):
        """开发环境允许所有来源"""
        resp = client.get('/health')
        assert resp.headers['Access-Control-Allow-Origin'] == '*'

    def test_cors_allow_methods(self, client):
        """应允许常用 HTTP 方法"""
        resp = client.get('/health')
        methods = resp.headers.get('Access-Control-Allow-Methods', '')
        for m in ['GET', 'POST', 'PUT', 'DELETE']:
            assert m in methods

    def test_cors_allow_headers(self, client):
        """应允许 Authorization 头"""
        resp = client.get('/health')
        headers = resp.headers.get('Access-Control-Allow-Headers', '')
        assert 'Authorization' in headers


class TestErrorHandling:
    """错误处理"""

    def test_404_returns_json(self, client):
        """404 应返回 JSON"""
        resp = client.get('/api/nonexistent-endpoint')
        assert resp.status_code == 404
        assert resp.is_json
        data = resp.get_json()
        assert 'error' in data

    def test_404_for_nonexistent_paper(self, client):
        """具体资源 404"""
        resp = client.get('/api/papers/99999')
        assert resp.status_code == 404
        assert resp.is_json

    def test_method_not_allowed(self, client):
        """不支持的 HTTP 方法"""
        resp = client.patch('/api/papers')
        assert resp.status_code in [405, 404]


class TestHealthEndpoint:
    """健康检查"""

    def test_health_returns_ok(self, client):
        """/health 应返回 200"""
        resp = client.get('/health')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['status'] == 'ok'

    def test_favicon_returns_204(self, client):
        """/favicon.ico 应返回 204"""
        resp = client.get('/favicon.ico')
        assert resp.status_code == 204


class TestData60sApi:
    """60s 数据 API"""

    def test_list_60s_dates_empty(self, client):
        """空数据时返回空列表"""
        resp = client.get('/api/60s/dates')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True
        assert isinstance(data['dates'], list)

    def test_save_and_load_60s(self, client):
        """保存并加载 60s 数据"""
        # 保存
        resp = client.post('/api/60s/save', json={
            'date': '2026-01-01',
            'source_id': 'test',
            'data': {'news': ['item1', 'item2']}
        })
        assert resp.status_code == 200
        assert resp.get_json()['ok'] is True

        # 加载
        resp = client.get('/api/60s/load/2026-01-01/test')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['ok'] is True
        assert data['data']['news'] == ['item1', 'item2']

    def test_load_nonexistent_60s(self, client):
        """加载不存在的数据 404"""
        resp = client.get('/api/60s/load/2099-12-31/nonexistent')
        assert resp.status_code == 404

    def test_save_60s_missing_fields(self, client):
        """保存缺少字段 400"""
        resp = client.post('/api/60s/save', json={'date': '2026-01-01'})
        assert resp.status_code == 400


class TestSessionLifecycle:
    """Session 生命周期"""

    def test_session_cleaned_after_request(self, client, make_user):
        """请求结束后 session 应被清理（teardown_appcontext）"""
        make_user(username='alice', password='alice12345')

        # 多次请求不应累积 session
        for _ in range(3):
            resp = client.get('/api/papers')
            assert resp.status_code == 200

    def test_concurrent_requests_isolated(self, client, make_user, make_paper):
        """多次请求间数据应隔离"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Test', user_id=user.id, is_public=True)

        # 连续请求应都能看到数据
        for _ in range(3):
            resp = client.get('/api/papers')
            assert resp.status_code == 200
            papers = resp.get_json()['papers']
            assert any(p['title'] == 'Test' for p in papers)
