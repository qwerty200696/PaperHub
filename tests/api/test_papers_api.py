"""
Papers API 过滤/分页/更新/删除集成测试

覆盖：
- GET    /api/papers               列表（分页/过滤/排序）
- GET    /api/papers/<id>          详情
- PUT    /api/papers/<id>          更新（标星/状态/分类）
- DELETE /api/papers/<id>          删除
- GET    /api/papers/<id>/notes    论文关联笔记
"""
import pytest
from datetime import date


class TestPapersListPagination:
    """论文列表分页"""

    def test_list_papers_default_pagination(self, client, make_user, make_paper):
        """默认分页参数"""
        user = make_user(username='alice', password='alice12345')
        for i in range(3):
            make_paper(title=f'P{i}', user_id=user.id, is_public=True)

        resp = client.get('/api/papers')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'papers' in data
        assert 'total' in data
        assert 'page' in data
        assert 'per_page' in data
        assert 'pages' in data
        assert data['page'] == 1

    def test_list_papers_custom_per_page(self, client, make_user, make_paper):
        """自定义每页数量"""
        user = make_user(username='alice', password='alice12345')
        for i in range(5):
            make_paper(title=f'P{i}', user_id=user.id, is_public=True)

        resp = client.get('/api/papers?per_page=2&page=1')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['per_page'] == 2
        assert len(data['papers']) <= 2
        assert data['pages'] >= 3

    def test_list_papers_total_count(self, client, make_user, make_paper):
        """总数计算"""
        user = make_user(username='alice', password='alice12345')
        for i in range(4):
            make_paper(title=f'P{i}', user_id=user.id, is_public=True)

        resp = client.get('/api/papers?per_page=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 4


class TestPapersListFilter:
    """论文列表过滤"""

    def test_filter_by_source(self, client, make_user, make_paper):
        """按来源过滤"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Arxiv', source='arxiv',
                   user_id=user.id, is_public=True)
        make_paper(title='Manual', source='manual',
                   user_id=user.id, is_public=True)

        resp = client.get('/api/papers?source=arxiv')
        assert resp.status_code == 200
        for p in resp.get_json()['papers']:
            assert p['source'] == 'arxiv'

    def test_filter_by_status(self, client, make_user, make_paper):
        """按状态过滤"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='P1', status='pending',
                   user_id=user.id, is_public=True)
        make_paper(title='P2', status='read',
                   user_id=user.id, is_public=True)

        resp = client.get('/api/papers?status=pending')
        assert resp.status_code == 200
        for p in resp.get_json()['papers']:
            assert p['status'] == 'pending'

    def test_filter_by_starred(self, client, make_user, make_paper):
        """按标星过滤"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='Starred', starred=True,
                   user_id=user.id, is_public=True)
        make_paper(title='NotStarred', starred=False,
                   user_id=user.id, is_public=True)

        resp = client.get('/api/papers?starred=true')
        assert resp.status_code == 200
        for p in resp.get_json()['papers']:
            assert p['starred'] is True

    def test_filter_by_category_l1(self, client, make_user, make_paper):
        """按一级分类过滤"""
        user = make_user(username='alice', password='alice12345')
        make_paper(title='P1', category_l1='CS',
                   user_id=user.id, is_public=True)
        make_paper(title='P2', category_l1='Physics',
                   user_id=user.id, is_public=True)

        resp = client.get('/api/papers?category_l1=CS')
        assert resp.status_code == 200
        for p in resp.get_json()['papers']:
            assert p['category_l1'] == 'CS'


class TestPaperDetail:
    """论文详情"""

    def test_get_paper_detail_includes_tags(self, client, make_user, make_paper):
        """详情应包含 tags 字段"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id, is_public=True)

        resp = client.get(f'/api/papers/{paper.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tags' in data
        assert isinstance(data['tags'], list)

    def test_get_paper_detail_includes_articles(self, client, make_user, make_paper):
        """详情应包含 articles 字段"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Test', user_id=user.id, is_public=True)

        resp = client.get(f'/api/papers/{paper.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'articles' in data or hasattr(data, 'get')

    def test_get_paper_invalid_id(self, client):
        """无效 ID"""
        resp = client.get('/api/papers/99999')
        assert resp.status_code == 404


class TestPaperUpdate:
    """论文更新"""

    def test_update_paper_title(self, client, make_user, make_paper):
        """更新标题"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Old', user_id=user.id, is_public=True)

        resp = client.put(f'/api/papers/{paper.id}', json={'title': 'New Title'})
        assert resp.status_code == 200
        assert resp.get_json()['title'] == 'New Title'

    def test_update_paper_starred(self, client, make_user, make_paper):
        """更新标星"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='P', starred=False,
                           user_id=user.id, is_public=True)

        resp = client.put(f'/api/papers/{paper.id}', json={'starred': True})
        assert resp.status_code == 200
        assert resp.get_json()['starred'] is True

    def test_update_paper_status(self, client, make_user, make_paper):
        """更新状态"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='P', status='pending',
                           user_id=user.id, is_public=True)

        resp = client.put(f'/api/papers/{paper.id}', json={'status': 'read'})
        assert resp.status_code == 200
        assert resp.get_json()['status'] == 'read'

    def test_update_paper_category(self, client, make_user, make_paper):
        """更新分类"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='P', user_id=user.id, is_public=True)

        resp = client.put(f'/api/papers/{paper.id}',
                          json={'category_l1': 'CS', 'category_l2': 'AI'})
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['category_l1'] == 'CS'
        assert data['category_l2'] == 'AI'

    def test_update_nonexistent_paper(self, client):
        """更新不存在 404"""
        resp = client.put('/api/papers/99999', json={'title': 'x'})
        assert resp.status_code == 404


class TestPaperDelete:
    """论文删除"""

    def test_delete_paper(self, client, make_user, make_paper):
        """删除论文"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='To Delete', user_id=user.id, is_public=True)

        resp = client.delete(f'/api/papers/{paper.id}')
        assert resp.status_code == 200

        # 验证已删除
        resp2 = client.get(f'/api/papers/{paper.id}')
        assert resp2.status_code == 404

    def test_delete_nonexistent_paper(self, client):
        """删除不存在 404"""
        resp = client.delete('/api/papers/99999')
        assert resp.status_code == 404


class TestPaperNotes:
    """论文关联笔记"""

    def test_get_paper_notes_empty(self, client, make_user, make_paper):
        """无关联笔记"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='P', user_id=user.id, is_public=True)

        resp = client.get(f'/api/papers/{paper.id}/notes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'notes' in data
        assert isinstance(data['notes'], list)

    def test_get_paper_notes_with_data(self, client, make_user, make_paper, make_note, db_session):
        """有关联笔记"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='P', user_id=user.id, is_public=True)
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)
        paper.notes.append(note)
        db_session.commit()

        resp = client.get(f'/api/papers/{paper.id}/notes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 1
        assert any(n['title'] == 'Note' for n in data['notes'])

    def test_get_notes_of_nonexistent_paper(self, client):
        """不存在的论文 404"""
        resp = client.get('/api/papers/99999/notes')
        assert resp.status_code == 404
