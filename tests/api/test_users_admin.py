"""
用户管理 API 集成测试

覆盖：
- GET  /api/users          用户列表（仅管理员）
- PUT  /api/users/<id>     更新用户信息
"""
import pytest


class TestListUsers:
    """用户列表 API 测试"""

    def test_admin_can_list_users(self, client, make_user, auth_headers):
        """管理员可查看用户列表"""
        make_user(username='admin', password='admin12345', is_admin=True)
        make_user(username='alice', password='alice12345')
        make_user(username='bob', password='bob12345678')
        h = auth_headers('admin', 'admin12345')

        resp = client.get('/api/users', headers=h)

        assert resp.status_code == 200
        users = resp.get_json()['users']
        assert len(users) >= 3
        usernames = [u['username'] for u in users]
        assert 'admin' in usernames
        assert 'alice' in usernames
        assert 'bob' in usernames

    def test_normal_user_cannot_list_users(self, client, make_user, auth_headers):
        """普通用户不能查看用户列表"""
        make_user(username='admin', password='admin12345', is_admin=True)
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        resp = client.get('/api/users', headers=h)
        assert resp.status_code == 403
        assert resp.get_json()['code'] == 'FORBIDDEN'

    def test_list_users_without_token(self, client):
        """无 token 应返回 401"""
        resp = client.get('/api/users')
        assert resp.status_code == 401

    def test_list_users_excludes_password_hash(self, client, make_user, auth_headers):
        """用户列表不应包含 password_hash"""
        make_user(username='admin', password='admin12345', is_admin=True)
        h = auth_headers('admin', 'admin12345')

        resp = client.get('/api/users', headers=h)
        for user in resp.get_json()['users']:
            assert 'password_hash' not in user


class TestUpdateUser:
    """更新用户信息 API 测试"""

    def test_update_self_display_name(self, client, make_user, auth_headers):
        """用户可修改自己的 display_name"""
        user = make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        resp = client.put(f'/api/users/{user.id}',
                          headers=h,
                          json={'display_name': 'Alice Updated'})

        assert resp.status_code == 200
        assert resp.get_json()['user']['display_name'] == 'Alice Updated'

    def test_update_self_password_with_old(self, client, make_user, auth_headers):
        """用户修改自己密码需提供旧密码"""
        user = make_user(username='alice', password='oldpass12345')
        h = auth_headers('alice', 'oldpass12345')

        resp = client.put(f'/api/users/{user.id}',
                          headers=h,
                          json={'password': 'newpass12345',
                                'old_password': 'oldpass12345'})

        assert resp.status_code == 200

        # 用新密码登录
        login_resp = client.post('/api/auth/login', json={
            'username': 'alice',
            'password': 'newpass12345'
        })
        assert login_resp.status_code == 200

    def test_update_self_password_wrong_old(self, client, make_user, auth_headers):
        """旧密码错误应返回 400"""
        user = make_user(username='alice', password='oldpass12345')
        h = auth_headers('alice', 'oldpass12345')

        resp = client.put(f'/api/users/{user.id}',
                          headers=h,
                          json={'password': 'newpass12345',
                                'old_password': 'wrongoldpass'})

        assert resp.status_code == 400
        assert resp.get_json()['code'] == 'INVALID_OLD_PASSWORD'

    def test_update_other_user_forbidden(self, client, make_user, auth_headers):
        """普通用户不能修改他人信息"""
        make_user(username='admin', password='admin12345', is_admin=True)
        alice = make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        # alice 尝试修改 admin
        resp = client.put('/api/users/1',  # admin 的 id
                          headers=h,
                          json={'display_name': 'hacked'})

        assert resp.status_code == 403

    def test_admin_can_update_others(self, client, make_user, auth_headers):
        """管理员可修改他人信息"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        alice = make_user(username='alice', password='alice12345')
        h = auth_headers('admin', 'admin12345')

        resp = client.put(f'/api/users/{alice.id}',
                          headers=h,
                          json={'display_name': 'Alice by Admin'})

        assert resp.status_code == 200
        assert resp.get_json()['user']['display_name'] == 'Alice by Admin'

    def test_admin_can_reset_others_password_without_old(self, client, make_user, auth_headers):
        """管理员重置他人密码不需要旧密码"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        alice = make_user(username='alice', password='alice12345')
        h = auth_headers('admin', 'admin12345')

        resp = client.put(f'/api/users/{alice.id}',
                          headers=h,
                          json={'password': 'resetpass12345'})

        assert resp.status_code == 200

        # 用新密码登录
        login_resp = client.post('/api/auth/login', json={
            'username': 'alice',
            'password': 'resetpass12345'
        })
        assert login_resp.status_code == 200

    def test_admin_can_grant_admin(self, client, make_user, auth_headers):
        """管理员可授予他人管理员权限"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        alice = make_user(username='alice', password='alice12345')
        h = auth_headers('admin', 'admin12345')

        resp = client.put(f'/api/users/{alice.id}',
                          headers=h,
                          json={'is_admin': True})

        assert resp.status_code == 200
        assert resp.get_json()['user']['is_admin'] is True

    def test_admin_cannot_demote_self(self, client, make_user, auth_headers):
        """管理员不能取消自己的管理员权限"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        h = auth_headers('admin', 'admin12345')

        resp = client.put(f'/api/users/{admin.id}',
                          headers=h,
                          json={'is_admin': False})

        assert resp.status_code == 400

    def test_admin_cannot_disable_self(self, client, make_user, auth_headers):
        """管理员不能禁用自己"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        h = auth_headers('admin', 'admin12345')

        resp = client.put(f'/api/users/{admin.id}',
                          headers=h,
                          json={'is_active': False})

        assert resp.status_code == 400

    def test_update_nonexistent_user(self, client, make_user, auth_headers):
        """更新不存在的用户应返回 404"""
        make_user(username='admin', password='admin12345', is_admin=True)
        h = auth_headers('admin', 'admin12345')

        resp = client.put('/api/users/9999',
                          headers=h,
                          json={'display_name': 'ghost'})

        assert resp.status_code == 404

    def test_update_password_too_short(self, client, make_user, auth_headers):
        """新密码过短应返回 400"""
        user = make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        resp = client.put(f'/api/users/{user.id}',
                          headers=h,
                          json={'password': 'short',
                                'old_password': 'alice12345'})

        assert resp.status_code == 400
