"""
UserPaperStatus 模型单元测试

覆盖：
- 表结构
- 唯一约束（user_id + paper_id）
- 默认值
- to_dict 序列化
"""
import pytest

from backend.models import UserPaperStatus, User, Paper


class TestUserPaperStatusModel:
    """UserPaperStatus 模型测试"""

    def test_create_status(self, db_session, make_user, make_paper):
        """创建用户论文状态记录"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id, is_public=False)

        status = UserPaperStatus(
            user_id=user.id,
            paper_id=paper.id,
            starred=True,
            read_status='read',
            read_progress=100,
        )
        db_session.add(status)
        db_session.commit()

        assert status.id is not None
        assert status.user_id == user.id
        assert status.paper_id == paper.id
        assert status.starred is True
        assert status.read_status == 'read'
        assert status.read_progress == 100

    def test_default_values(self, db_session, make_user, make_paper):
        """默认值测试"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id)

        status = UserPaperStatus(user_id=user.id, paper_id=paper.id)
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)

        assert status.starred is False
        assert status.read_status == 'unread'
        assert status.read_progress == 0
        assert status.last_read_at is None

    def test_unique_constraint(self, db_session, make_user, make_paper):
        """同一 user+paper 组合应唯一"""
        from sqlalchemy.exc import IntegrityError

        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id)

        s1 = UserPaperStatus(user_id=user.id, paper_id=paper.id)
        db_session.add(s1)
        db_session.commit()

        # 同一 user+paper 再创建应失败
        with pytest.raises(IntegrityError):
            s2 = UserPaperStatus(user_id=user.id, paper_id=paper.id)
            db_session.add(s2)
            db_session.commit()
        db_session.rollback()

    def test_different_users_same_paper(self, db_session, make_user, make_paper):
        """不同用户对同一论文可有独立状态"""
        alice = make_user(username='alice', password='alice12345')
        bob = make_user(username='bob', password='bob12345678')
        paper = make_paper(title='Shared', user_id=alice.id, is_public=True)

        # alice 标星
        s_alice = UserPaperStatus(user_id=alice.id, paper_id=paper.id, starred=True, read_status='read')
        # bob 未标星
        s_bob = UserPaperStatus(user_id=bob.id, paper_id=paper.id, starred=False, read_status='unread')

        db_session.add_all([s_alice, s_bob])
        db_session.commit()

        assert s_alice.starred is True
        assert s_bob.starred is False
        assert s_alice.read_status == 'read'
        assert s_bob.read_status == 'unread'

    def test_to_dict(self, db_session, make_user, make_paper):
        """to_dict 序列化"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id)

        status = UserPaperStatus(
            user_id=user.id,
            paper_id=paper.id,
            starred=True,
            read_status='reading',
            read_progress=45,
        )
        db_session.add(status)
        db_session.commit()
        db_session.refresh(status)

        d = status.to_dict()
        assert d['user_id'] == user.id
        assert d['paper_id'] == paper.id
        assert d['starred'] is True
        assert d['read_status'] == 'reading'
        assert d['read_progress'] == 45
        assert 'created_at' in d
        assert 'updated_at' in d

    def test_read_status_values(self, db_session, make_user, make_paper):
        """阅读状态支持 unread / reading / read"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id)

        for status_val in ['unread', 'reading', 'read']:
            s = UserPaperStatus(
                user_id=user.id,
                paper_id=paper.id,
                read_status=status_val,
            )
            db_session.add(s)
            db_session.commit()
            db_session.refresh(s)
            assert s.read_status == status_val
            # 清理以便下一个状态可创建（唯一约束）
            db_session.delete(s)
            db_session.commit()
