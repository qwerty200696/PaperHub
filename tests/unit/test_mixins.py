"""
UserOwnedMixin 单元测试

覆盖：
- visible_to() 可见性逻辑
- owned_by() 归属判断
- to_dict_with_owner() 序列化
- 公共/私有数据隔离
- 管理员权限
- 无用户场景（灰度阶段）
"""
import pytest

from backend.models import Paper, Tag, Note, Article, WechatSubscription, WechatConfig
from backend.models.mixins import UserOwnedMixin


class FakeUser:
    """测试用 FakeUser，避免数据库依赖"""
    def __init__(self, id, is_admin=False):
        self.id = id
        self.is_admin = is_admin


class TestVisibleTo:
    """visible_to() 可见性逻辑"""

    def test_public_data_visible_to_anyone(self):
        """公共数据对任何登录用户可见"""
        owner = FakeUser(1)
        other = FakeUser(2)
        admin = FakeUser(3, is_admin=True)

        p = Paper(is_public=True, user_id=1)
        assert p.visible_to(owner) is True
        assert p.visible_to(other) is True
        assert p.visible_to(admin) is True

    def test_private_data_only_visible_to_owner(self):
        """私有数据仅 owner 和 admin 可见"""
        owner = FakeUser(1)
        other = FakeUser(2)
        admin = FakeUser(3, is_admin=True)

        p = Paper(is_public=False, user_id=1)
        assert p.visible_to(owner) is True
        assert p.visible_to(other) is False
        assert p.visible_to(admin) is True

    def test_no_user_only_sees_public(self):
        """无用户场景（灰度阶段）：仅公共数据可见"""
        p_public = Paper(is_public=True, user_id=1)
        p_private = Paper(is_public=False, user_id=1)

        assert p_public.visible_to(None) is True
        assert p_private.visible_to(None) is False

    def test_admin_sees_everything(self):
        """管理员可见所有数据"""
        admin = FakeUser(99, is_admin=True)

        p_private_others = Paper(is_public=False, user_id=1)
        p_public_others = Paper(is_public=True, user_id=1)
        p_private_self = Paper(is_public=False, user_id=99)

        assert p_private_others.visible_to(admin) is True
        assert p_public_others.visible_to(admin) is True
        assert p_private_self.visible_to(admin) is True


class TestOwnedBy:
    """owned_by() 归属判断"""

    def test_owner_owns(self):
        """owner 可拥有"""
        owner = FakeUser(1)
        p = Paper(user_id=1)
        assert p.owned_by(owner) is True

    def test_other_does_not_own(self):
        """非 owner 不拥有"""
        other = FakeUser(2)
        p = Paper(user_id=1)
        assert p.owned_by(other) is False

    def test_admin_owns_everything(self):
        """管理员拥有所有数据"""
        admin = FakeUser(99, is_admin=True)
        p = Paper(user_id=1)
        assert p.owned_by(admin) is True

    def test_no_user_owns_nothing(self):
        """无用户不拥有任何数据"""
        p = Paper(user_id=1)
        assert p.owned_by(None) is False

    def test_public_data_not_owned_by_other(self):
        """公共数据不等于其他用户拥有"""
        other = FakeUser(2)
        p = Paper(is_public=True, user_id=1)
        # 公共数据对 other 可见，但不归 other 拥有
        assert p.visible_to(other) is True
        assert p.owned_by(other) is False


class TestMixinAppliedToAllModels:
    """验证所有业务模型都继承了 UserOwnedMixin"""

    def test_all_business_models_inherit_mixin(self):
        """6 个业务模型应继承 UserOwnedMixin"""
        for cls in [Paper, Tag, Note, Article, WechatSubscription, WechatConfig]:
            assert issubclass(cls, UserOwnedMixin), f'{cls.__name__} 未继承 UserOwnedMixin'

    def test_all_models_have_user_id_column(self):
        """所有业务模型应有 user_id 属性"""
        for cls in [Paper, Tag, Note, Article, WechatSubscription, WechatConfig]:
            assert hasattr(cls, 'user_id'), f'{cls.__name__} 缺少 user_id'

    def test_all_models_have_is_public_column(self):
        """所有业务模型应有 is_public 属性"""
        for cls in [Paper, Tag, Note, Article, WechatSubscription, WechatConfig]:
            assert hasattr(cls, 'is_public'), f'{cls.__name__} 缺少 is_public'


class TestToDictWithOwner:
    """to_dict_with_owner() 序列化"""

    def test_to_dict_includes_owner_fields(self, db_session, make_paper):
        """to_dict 应包含 user_id / is_public"""
        paper = make_paper(title='Test', user_id=1, is_public=True)
        d = paper.to_dict()

        assert 'user_id' in d
        assert 'is_public' in d
        assert d['user_id'] == 1
        assert d['is_public'] is True

    def test_to_dict_with_owner_helper(self):
        """to_dict_with_owner 工具方法"""
        p = Paper(title='Test', user_id=1, is_public=False)
        base = {'id': 1, 'title': 'Test'}
        result = p.to_dict_with_owner(base)

        assert result['user_id'] == 1
        assert result['is_public'] is False
        assert result['title'] == 'Test'


class TestIsolationScenarios:
    """综合隔离场景测试"""

    def test_scenario_two_users_private_data(self, db_session, make_user, make_paper):
        """场景：两个用户各自的私有数据互不可见"""
        alice = make_user(username='alice', password='alice12345')
        bob = make_user(username='bob', password='bob12345678')

        # alice 的私有论文
        alice_paper = make_paper(title='Alice Private', user_id=alice.id, is_public=False)
        # bob 的私有论文
        bob_paper = make_paper(title='Bob Private', user_id=bob.id, is_public=False)

        # alice 看不到 bob 的私有
        assert bob_paper.visible_to(alice) is False
        # bob 看不到 alice 的私有
        assert alice_paper.visible_to(bob) is False
        # 各自看自己的 OK
        assert alice_paper.visible_to(alice) is True
        assert bob_paper.visible_to(bob) is True

    def test_scenario_public_data_shared(self, db_session, make_user, make_paper):
        """场景：公共数据所有用户可见，但只有 owner 可修改"""
        alice = make_user(username='alice', password='alice12345')
        bob = make_user(username='bob', password='bob12345678')

        # alice 创建公共论文
        public_paper = make_paper(title='Shared', user_id=alice.id, is_public=True)

        # bob 可见
        assert public_paper.visible_to(bob) is True
        # 但 bob 不拥有（不能修改/删除）
        assert public_paper.owned_by(bob) is False
        # alice 拥有
        assert public_paper.owned_by(alice) is True

    def test_scenario_admin_override(self, db_session, make_user, make_paper):
        """场景：管理员可访问和拥有所有数据"""
        admin = make_user(username='admin', password='admin12345', is_admin=True)
        alice = make_user(username='alice', password='alice12345')

        # alice 的私有论文
        alice_private = make_paper(title='Alice Private', user_id=alice.id, is_public=False)

        # admin 可见且可拥有
        assert alice_private.visible_to(admin) is True
        assert alice_private.owned_by(admin) is True
