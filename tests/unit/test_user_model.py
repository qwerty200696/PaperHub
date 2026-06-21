"""
User 模型单元测试

覆盖：
- 密码哈希（bcrypt）
- 密码校验
- to_dict 序列化
- 字段默认值
- 唯一约束
"""
import pytest

from backend.models import User


class TestPasswordHashing:
    """密码哈希测试"""

    def test_set_password_generates_bcrypt_hash(self, db_session):
        """设置密码应生成 bcrypt 哈希"""
        user = User(username='alice', display_name='Alice')
        user.set_password('mypassword123')

        assert user.password_hash is not None
        assert user.password_hash != 'mypassword123'
        # bcrypt 哈希以 $2b$ 开头
        assert user.password_hash.startswith('$2')

    def test_password_hash_is_salt_unique(self, db_session):
        """相同密码两次哈希应不同（盐随机）"""
        u1 = User(username='u1')
        u1.set_password('samepassword')
        u2 = User(username='u2')
        u2.set_password('samepassword')

        assert u1.password_hash != u2.password_hash

    def test_check_password_correct(self, db_session):
        """正确密码应通过校验"""
        user = User(username='alice')
        user.set_password('correct_password_123')

        assert user.check_password('correct_password_123') is True

    def test_check_password_wrong(self, db_session):
        """错误密码应不通过"""
        user = User(username='alice')
        user.set_password('correct_password_123')

        assert user.check_password('wrong') is False
        assert user.check_password('') is False
        assert user.check_password('CORRECT_PASSWORD_123') is False  # 大小写敏感

    def test_check_password_empty_hash(self, db_session):
        """password_hash 为空时校验应返回 False"""
        user = User(username='alice')
        user.password_hash = ''
        assert user.check_password('anything') is False

    def test_check_password_invalid_hash(self, db_session):
        """password_hash 格式无效时应返回 False 而非抛异常"""
        user = User(username='alice')
        user.password_hash = 'not-a-valid-bcrypt-hash'
        assert user.check_password('anything') is False


class TestUserModel:
    """User 模型基础测试"""

    def test_create_user(self, db_session):
        """创建用户并保存"""
        user = User(
            username='newuser',
            display_name='New User',
            is_admin=False,
            is_active=True,
        )
        user.set_password('password12345')
        db_session.add(user)
        db_session.commit()

        assert user.id is not None
        assert user.username == 'newuser'
        assert user.is_admin is False
        assert user.is_active is True
        assert user.created_at is not None

    def test_username_unique_constraint(self, db_session, make_user):
        """用户名唯一约束"""
        make_user(username='dup', password='pass12345')
        db_session.commit()

        # 创建同名用户应抛异常
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            u2 = User(username='dup')
            u2.set_password('pass12345')
            db_session.add(u2)
            db_session.commit()
        db_session.rollback()

    def test_default_is_admin_false(self, db_session):
        """新用户默认非管理员"""
        user = User(username='normal')
        user.set_password('pass12345')
        db_session.add(user)
        db_session.commit()

        assert user.is_admin is False

    def test_default_is_active_true(self, db_session):
        """新用户默认激活"""
        user = User(username='normal')
        user.set_password('pass12345')
        db_session.add(user)
        db_session.commit()

        assert user.is_active is True

    def test_to_dict_excludes_password_hash(self, db_session, make_user):
        """to_dict 不应包含 password_hash"""
        user = make_user(username='alice', password='pass12345')
        d = user.to_dict()

        assert 'password_hash' not in d
        assert d['username'] == 'alice'
        assert d['is_admin'] is False
        assert d['is_active'] is True
        assert 'created_at' in d
        assert 'updated_at' in d

    def test_updated_at_changes_on_update(self, db_session, make_user):
        """更新记录时 updated_at 应变化"""
        import time
        user = make_user(username='alice', password='pass12345')
        original_updated = user.updated_at

        time.sleep(0.01)
        user.display_name = 'Alice Updated'
        db_session.commit()
        db_session.refresh(user)

        assert user.updated_at >= original_updated
