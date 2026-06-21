"""
Auth API 集成测试

覆盖：
- POST /api/auth/register  注册
- POST /api/auth/login     登录
- GET  /api/auth/me        当前用户
- POST /api/auth/logout    登出
"""
import pytest


class TestRegister:
    """注册 API 测试"""

    def test_register_first_user_becomes_admin(self, client):
        """首个注册用户自动成为管理员"""
        resp = client.post('/api/auth/register', json={
            'username': 'firstuser',
            'password': 'password12345',
            'display_name': 'First User'
        })

        assert resp.status_code == 201
        data = resp.get_json()
        assert data['message'] == '注册成功'
        assert data['token'] is not None
        assert data['user']['username'] == 'firstuser'
        assert data['user']['is_admin'] is True

    def test_register_second_user_is_not_admin(self, client, make_user):
        """第二个注册用户为普通用户"""
        # 先创建一个 admin
        make_user(username='admin', password='admin12345', is_admin=True)

        resp = client.post('/api/auth/register', json={
            'username': 'second',
            'password': 'password12345'
        })

        assert resp.status_code == 201
        assert resp.get_json()['user']['is_admin'] is False

    def test_register_duplicate_username(self, client, make_user):
        """重复用户名应返回 409"""
        make_user(username='dup', password='pass12345')

        resp = client.post('/api/auth/register', json={
            'username': 'dup',
            'password': 'anotherpass123'
        })

        assert resp.status_code == 409
        assert resp.get_json()['code'] == 'USERNAME_EXISTS'

    def test_register_short_username(self, client):
        """用户名过短应返回 400"""
        resp = client.post('/api/auth/register', json={
            'username': 'ab',  # 少于 3 字符
            'password': 'password12345'
        })

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'VALIDATION_ERROR'

    def test_register_short_password(self, client):
        """密码过短应返回 400"""
        resp = client.post('/api/auth/register', json={
            'username': 'newuser',
            'password': '123'  # 少于 8 字符
        })

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'VALIDATION_ERROR'

    def test_register_empty_username(self, client):
        """空用户名应返回 400"""
        resp = client.post('/api/auth/register', json={
            'username': '',
            'password': 'password12345'
        })
        assert resp.status_code == 400

    def test_register_empty_password(self, client):
        """空密码应返回 400"""
        resp = client.post('/api/auth/register', json={
            'username': 'newuser',
            'password': ''
        })
        assert resp.status_code == 400

    def test_register_invalid_username_chars(self, client):
        """用户名含非法字符应返回 400"""
        resp = client.post('/api/auth/register', json={
            'username': 'user@name!',  # 含特殊字符
            'password': 'password12345'
        })
        assert resp.status_code == 400

    def test_register_no_json_body(self, client):
        """无 JSON body 应返回 400"""
        resp = client.post('/api/auth/register')
        assert resp.status_code == 400

    def test_register_returns_valid_token(self, client):
        """注册返回的 token 应可用于 /me"""
        resp = client.post('/api/auth/register', json={
            'username': 'newuser',
            'password': 'password12345'
        })
        token = resp.get_json()['token']

        # 用 token 访问 /me
        me_resp = client.get('/api/auth/me',
                             headers={'Authorization': f'Bearer {token}'})
        assert me_resp.status_code == 200
        assert me_resp.get_json()['user']['username'] == 'newuser'


class TestLogin:
    """登录 API 测试"""

    def test_login_success(self, client, make_user):
        """正确凭据登录成功"""
        make_user(username='alice', password='alice12345')

        resp = client.post('/api/auth/login', json={
            'username': 'alice',
            'password': 'alice12345'
        })

        assert resp.status_code == 200
        data = resp.get_json()
        assert data['message'] == '登录成功'
        assert data['token'] is not None
        assert data['user']['username'] == 'alice'

    def test_login_wrong_password(self, client, make_user):
        """错误密码应返回 401"""
        make_user(username='alice', password='alice12345')

        resp = client.post('/api/auth/login', json={
            'username': 'alice',
            'password': 'wrongpassword'
        })

        assert resp.status_code == 401
        assert resp.get_json()['code'] == 'INVALID_CREDENTIALS'

    def test_login_nonexistent_user(self, client):
        """不存在的用户应返回 401"""
        resp = client.post('/api/auth/login', json={
            'username': 'ghost',
            'password': 'anything'
        })

        assert resp.status_code == 401
        assert resp.get_json()['code'] == 'INVALID_CREDENTIALS'

    def test_login_empty_credentials(self, client):
        """空凭据应返回 400"""
        resp = client.post('/api/auth/login', json={
            'username': '',
            'password': ''
        })
        assert resp.status_code == 400

    def test_login_inactive_user(self, client, make_user):
        """被禁用的用户应返回 403"""
        make_user(username='inactive', password='pass12345', is_active=False)

        resp = client.post('/api/auth/login', json={
            'username': 'inactive',
            'password': 'pass12345'
        })

        assert resp.status_code == 403
        assert resp.get_json()['code'] == 'ACCOUNT_DISABLED'

    def test_login_case_sensitive_username(self, client, make_user):
        """用户名大小写敏感"""
        make_user(username='alice', password='pass12345')

        resp = client.post('/api/auth/login', json={
            'username': 'ALICE',  # 大写
            'password': 'pass12345'
        })

        assert resp.status_code == 401


class TestMe:
    """当前用户 API 测试"""

    def test_me_without_token(self, client):
        """无 token 访问 /me 应返回 401"""
        resp = client.get('/api/auth/me')
        assert resp.status_code == 401
        assert resp.get_json()['code'] == 'UNAUTHORIZED'

    def test_me_with_invalid_token(self, client):
        """无效 token 应返回 401"""
        resp = client.get('/api/auth/me',
                          headers={'Authorization': 'Bearer invalid.token.here'})
        assert resp.status_code == 401

    def test_me_with_malformed_header(self, client):
        """格式错误的 Authorization 头应返回 401"""
        resp = client.get('/api/auth/me',
                          headers={'Authorization': 'NotBearer abc'})
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client, make_user, auth_headers):
        """有效 token 应返回用户信息"""
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        resp = client.get('/api/auth/me', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['user']['username'] == 'alice'

    def test_me_returns_full_user_info(self, client, make_user, auth_headers):
        """/me 返回完整用户信息（不含 password_hash）"""
        make_user(username='alice', password='alice12345',
                  display_name='Alice Wang')
        h = auth_headers('alice', 'alice12345')

        resp = client.get('/api/auth/me', headers=h)
        user = resp.get_json()['user']

        assert user['username'] == 'alice'
        assert user['display_name'] == 'Alice Wang'
        assert 'password_hash' not in user
        assert 'id' in user
        assert 'is_admin' in user
        assert 'created_at' in user


class TestLogout:
    """登出 API 测试"""

    def test_logout_success(self, client, make_user, auth_headers):
        """登出成功应返回 200"""
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        resp = client.post('/api/auth/logout', headers=h)
        assert resp.status_code == 200
        assert resp.get_json()['message'] == '已登出'

    def test_logout_invalidates_token(self, client, make_user, auth_headers):
        """登出后旧 token 应失效"""
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        # 登出
        client.post('/api/auth/logout', headers=h)

        # 用旧 token 访问 /me 应失败
        resp = client.get('/api/auth/me', headers=h)
        assert resp.status_code == 401

    def test_logout_without_token(self, client):
        """无 token 登出应返回 401"""
        resp = client.post('/api/auth/logout')
        assert resp.status_code == 401

    def test_logout_twice_second_fails(self, client, make_user, auth_headers):
        """登出两次：第二次应失败"""
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        # 第一次登出成功
        resp1 = client.post('/api/auth/logout', headers=h)
        assert resp1.status_code == 200

        # 第二次登出失败（token 已黑名单）
        resp2 = client.post('/api/auth/logout', headers=h)
        assert resp2.status_code == 401
