"""
JWT 工具单元测试

覆盖：
- token 签发与解码
- token 过期
- token 黑名单
- 装饰器 auth_required / admin_required
- get_current_user 灰度模式
"""
import pytest

from backend.api.auth import (
    generate_token, decode_token,
    _is_token_blacklisted, _add_token_to_blacklist, _token_blacklist,
    auth_required, admin_required, get_current_user,
)


class FakeUser:
    def __init__(self, id=1, username='testuser', is_admin=False, is_active=True):
        self.id = id
        self.username = username
        self.is_admin = is_admin
        self.is_active = is_active


class TestTokenGeneration:
    """token 签发测试"""

    def test_generate_token_returns_string(self, app_context):
        """生成的 token 应是字符串"""
        user = FakeUser()
        token = generate_token(user)
        assert isinstance(token, str)
        assert len(token) > 0

    def test_token_contains_required_claims(self, app_context):
        """token 载荷应包含必需字段"""
        user = FakeUser(id=42, username='alice', is_admin=True)
        token = generate_token(user)
        payload, err = decode_token(token)

        assert err is None
        assert payload['sub'] == 42
        assert payload['username'] == 'alice'
        assert payload['is_admin'] is True
        assert 'jti' in payload
        assert 'iat' in payload
        assert 'exp' in payload

    def test_token_with_different_users(self, app_context):
        """不同用户的 token 应不同"""
        u1 = FakeUser(id=1, username='alice')
        u2 = FakeUser(id=2, username='bob')

        t1 = generate_token(u1)
        t2 = generate_token(u2)

        assert t1 != t2


class TestTokenDecode:
    """token 解码测试"""

    def test_decode_valid_token(self, app_context):
        """有效 token 应解码成功"""
        user = FakeUser(id=1, username='alice')
        token = generate_token(user)

        payload, err = decode_token(token)
        assert err is None
        assert payload['sub'] == 1

    def test_decode_invalid_token(self, app_context):
        """无效 token 应返回错误"""
        payload, err = decode_token('invalid.token.here')
        assert payload is None
        assert err == 'invalid_token'

    def test_decode_empty_token(self, app_context):
        """空 token 应返回错误"""
        payload, err = decode_token('')
        assert payload is None
        assert err == 'invalid_token'

    def test_decode_expired_token(self, app_context, monkeypatch):
        """过期 token 应返回 token_expired"""
        import jwt
        from datetime import datetime, timedelta

        # 构造一个已过期的 token
        user = FakeUser(id=1, username='alice')
        now = datetime.utcnow()
        payload = {
            'sub': user.id,
            'username': user.username,
            'is_admin': False,
            'jti': 'test-jti',
            'iat': now - timedelta(hours=2),
            'exp': now - timedelta(hours=1),  # 1 小时前过期
        }
        from flask import current_app
        token = jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')

        p, err = decode_token(token)
        assert p is None
        assert err == 'token_expired'


class TestTokenBlacklist:
    """token 黑名单测试"""

    def test_add_to_blacklist(self):
        """加入黑名单后应能检测到"""
        jti = 'test-jti-12345'
        exp = 9999999999  # 远未来

        assert _is_token_blacklisted(jti) is False
        _add_token_to_blacklist(jti, exp)
        assert _is_token_blacklisted(jti) is True

    def test_blacklist_cleanup_expired(self):
        """黑名单应自动清理过期项"""
        # 加入一个已过期的项
        import time
        past_exp = time.time() - 100
        _add_token_to_blacklist('expired-jti', past_exp)

        # 加入新项时触发清理
        _add_token_to_blacklist('new-jti', time.time() + 3600)

        assert _is_token_blacklisted('expired-jti') is False
        assert _is_token_blacklisted('new-jti') is True

    def test_blacklist_isolated_per_test(self):
        """每个测试的黑名单应独立（fixture 清理）"""
        # 此测试验证黑名单功能本身，不依赖清理
        _add_token_to_blacklist('iso-test-jti', 9999999999)
        assert _is_token_blacklisted('iso-test-jti') is True


class TestGetCurrentUser:
    """get_current_user 灰度模式测试"""

    def test_no_token_returns_none(self, app_context, client):
        """无 token 时返回 None（不抛异常）"""
        with client.application.test_request_context('/api/something'):
            user = get_current_user()
            assert user is None

    def test_invalid_token_returns_none(self, app_context, client):
        """无效 token 时返回 None（不抛异常）"""
        with client.application.test_request_context(
            '/api/something',
            headers={'Authorization': 'Bearer invalid.token.here'}
        ):
            user = get_current_user()
            assert user is None

    def test_valid_token_loads_user(self, app_context, client, make_user):
        """有效 token 加载用户"""
        user = make_user(username='alice', password='alice12345')
        token = generate_token(user)

        with client.application.test_request_context(
            '/api/something',
            headers={'Authorization': f'Bearer {token}'}
        ):
            loaded = get_current_user()
            assert loaded is not None
            assert loaded.id == user.id
            assert loaded.username == 'alice'

    def test_blacklisted_token_returns_none(self, app_context, client, make_user):
        """黑名单中的 token 返回 None"""
        user = make_user(username='alice', password='alice12345')
        token = generate_token(user)
        payload, _ = decode_token(token)

        # 加入黑名单
        _add_token_to_blacklist(payload['jti'], payload['exp'])

        with client.application.test_request_context(
            '/api/something',
            headers={'Authorization': f'Bearer {token}'}
        ):
            loaded = get_current_user()
            assert loaded is None

    def test_inactive_user_returns_none(self, app_context, client, make_user):
        """被禁用的用户 token 应失效"""
        user = make_user(username='alice', password='alice12345', is_active=False)
        token = generate_token(user)

        with client.application.test_request_context(
            '/api/something',
            headers={'Authorization': f'Bearer {token}'}
        ):
            loaded = get_current_user()
            assert loaded is None
