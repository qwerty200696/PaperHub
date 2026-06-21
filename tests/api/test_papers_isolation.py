"""
数据隔离 API 集成测试

覆盖：
- P2 阶段的 user_id / is_public 字段在 API 响应中可见
- to_dict 输出包含归属信息
- 现有 API 在 P2 阶段向后兼容（无 token 仍可访问公共数据）

注：完整的 API 级别数据隔离（A 用户看不到 B 用户私有数据）
    将在 P3 阶段业务 API 加 @auth_required 后补充。
    P2 阶段仅验证模型层与 API 响应字段。
"""
import pytest


class TestPaperApiIncludesOwnerFields:
    """论文 API 响应应包含归属字段"""

    def test_paper_list_includes_user_id_and_is_public(self, client, make_user, make_paper):
        """论文列表的每条记录应包含 user_id / is_public"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Test 1', user_id=user.id, is_public=True)
        make_paper(title='Test 2', user_id=user.id, is_public=False)

        resp = client.get('/api/papers')
        assert resp.status_code == 200

        data = resp.get_json()
        papers = data.get('papers', [])
        assert len(papers) >= 2

        for p in papers:
            assert 'user_id' in p
            assert 'is_public' in p

    def test_paper_detail_includes_owner_fields(self, client, make_user, make_paper):
        """论文详情应包含 user_id / is_public"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id, is_public=True)

        resp = client.get(f'/api/papers/{paper.id}')
        assert resp.status_code == 200

        p = resp.get_json()
        assert 'user_id' in p
        assert 'is_public' in p
        assert p['user_id'] == user.id
        assert p['is_public'] is True


class TestTagApiIncludesOwnerFields:
    """标签 API 响应应包含归属字段"""

    def test_tag_list_includes_owner_fields(self, client, make_user, make_tag):
        """标签列表应包含 user_id / is_public"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='tag1', user_id=user.id, is_public=True)
        make_tag(name='tag2', user_id=user.id, is_public=False)

        resp = client.get('/api/tags')
        assert resp.status_code == 200

        tags = resp.get_json()
        if isinstance(tags, dict):
            tags = tags.get('tags', [])
        for t in tags:
            assert 'user_id' in t
            assert 'is_public' in t


class TestBackwardCompatibility:
    """P2 阶段向后兼容性测试"""

    def test_papers_accessible_without_token(self, client, make_user, make_paper):
        """无 token 访问 papers 仍可用（灰度阶段）"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Public', user_id=user.id, is_public=True)

        resp = client.get('/api/papers')
        assert resp.status_code == 200

    def test_tags_accessible_without_token(self, client, make_user, make_tag):
        """无 token 访问 tags 仍可用"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='public-tag', user_id=user.id, is_public=True)

        resp = client.get('/api/tags')
        assert resp.status_code == 200

    def test_articles_accessible_without_token(self, client):
        """无 token 访问 articles 仍可用"""
        resp = client.get('/api/articles')
        # 即使空列表也应 200
        assert resp.status_code == 200

    def test_notes_accessible_without_token(self, client):
        """无 token 访问 notes 仍可用"""
        resp = client.get('/api/notes')
        assert resp.status_code == 200

    def test_auth_still_works_alongside(self, client, make_user, auth_headers):
        """认证 API 与业务 API 共存"""
        make_user(username='alice', password='alice12345')
        h = auth_headers('alice', 'alice12345')

        # 认证 API 可用
        me_resp = client.get('/api/auth/me', headers=h)
        assert me_resp.status_code == 200

        # 业务 API 也可用
        papers_resp = client.get('/api/papers')
        assert papers_resp.status_code == 200


class TestModelLevelIsolation:
    """模型层数据隔离测试（通过 API 创建数据后验证）"""

    def test_two_users_data_in_db(self, client, make_user, make_paper, db_session):
        """两个用户的数据共存于数据库，但归属不同"""
        from backend.models import Paper

        alice = make_user(username='alice', password='alice12345')
        bob = make_user(username='bob', password='bob12345678')

        alice_paper = make_paper(title='Alice Paper', user_id=alice.id, is_public=False)
        bob_paper = make_paper(title='Bob Paper', user_id=bob.id, is_public=False)

        # 数据库查询验证
        all_papers = db_session.query(Paper).all()
        alice_papers = [p for p in all_papers if p.user_id == alice.id]
        bob_papers = [p for p in all_papers if p.user_id == bob.id]

        assert any(p.title == 'Alice Paper' for p in alice_papers)
        assert any(p.title == 'Bob Paper' for p in bob_papers)
        # alice 的论文不在 bob 的列表中
        assert not any(p.title == 'Alice Paper' for p in bob_papers)

    def test_public_data_visible_to_all_via_model(self, client, make_user, make_paper):
        """公共数据通过模型层 visible_to 验证可见性"""
        alice = make_user(username='alice', password='alice12345')
        bob = make_user(username='bob', password='bob12345678')

        public_paper = make_paper(title='Public', user_id=alice.id, is_public=True)
        private_paper = make_paper(title='Private', user_id=alice.id, is_public=False)

        # bob 通过模型可见公共，不可见私有
        assert public_paper.visible_to(bob) is True
        assert private_paper.visible_to(bob) is False

        # alice 可见自己的所有
        assert public_paper.visible_to(alice) is True
        assert private_paper.visible_to(alice) is True
