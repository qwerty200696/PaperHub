"""
Notes API CRUD 集成测试

覆盖：
- GET    /api/notes               列表（含分页/搜索/排序）
- POST   /api/notes               创建（含重复检测）
- GET    /api/notes/<id>          详情
- PUT    /api/notes/<id>          更新
- DELETE /api/notes/<id>          删除
- POST   /api/notes/<id>/papers   关联论文
- DELETE /api/notes/<id>/papers/<pid>  取消关联
- POST   /api/notes/<id>/tags     添加标签
- POST   /api/notes/batch         批量操作
"""
import pytest


class TestNotesList:
    """笔记列表 API"""

    def test_list_notes_empty(self, client):
        """空数据库返回空列表"""
        resp = client.get('/api/notes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'notes' in data
        assert isinstance(data['notes'], list)
        assert data['total'] == 0

    def test_list_notes_with_data(self, client, make_user, make_note):
        """有数据时返回笔记列表"""
        user = make_user(username='alice', password='alice12345')
        make_note(title='Note 1', content='content 1',
                  user_id=user.id, is_public=True)
        make_note(title='Note 2', content='content 2',
                  user_id=user.id, is_public=True)

        resp = client.get('/api/notes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 2
        titles = [n['title'] for n in data['notes']]
        assert 'Note 1' in titles
        assert 'Note 2' in titles

    def test_list_notes_pagination(self, client, make_user, make_note):
        """分页参数"""
        user = make_user(username='alice', password='alice12345')
        for i in range(5):
            make_note(title=f'Note {i}', content=f'c{i}',
                      user_id=user.id, is_public=True)

        resp = client.get('/api/notes?page=1&per_page=2')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['page'] == 1
        assert data['per_page'] == 2
        assert len(data['notes']) <= 2
        assert data['total'] >= 5

    def test_list_notes_keyword_search(self, client, make_user, make_note):
        """关键词搜索"""
        user = make_user(username='alice', password='alice12345')
        make_note(title='Machine Learning Basics',
                  content='content', user_id=user.id, is_public=True)
        make_note(title='Physics Notes',
                  content='content', user_id=user.id, is_public=True)

        resp = client.get('/api/notes?q=Machine')
        assert resp.status_code == 200
        data = resp.get_json()
        assert any('Machine' in n['title'] for n in data['notes'])

    def test_list_notes_filter_by_source(self, client, make_user, make_note):
        """按来源过滤"""
        user = make_user(username='alice', password='alice12345')
        make_note(title='Manual', content='c', source='manual',
                  user_id=user.id, is_public=True)
        make_note(title='AI Note', content='c', source='AI解读',
                  user_id=user.id, is_public=True)

        resp = client.get('/api/notes?source=manual')
        assert resp.status_code == 200
        data = resp.get_json()
        for n in data['notes']:
            assert n['source'] == 'manual'


class TestNoteCreate:
    """笔记创建 API"""

    def test_create_note_basic(self, client):
        """基础创建"""
        resp = client.post('/api/notes', json={
            'title': 'New Note',
            'content': 'hello world',
            'source': 'manual'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['success'] is True
        assert data['note']['title'] == 'New Note'
        assert data['id'] is not None

    def test_create_note_without_title(self, client):
        """无标题也能创建（title 可为 None）"""
        resp = client.post('/api/notes', json={
            'content': 'no title content'
        })
        assert resp.status_code == 201

    def test_create_note_with_paper_association(self, client, make_user, make_paper):
        """创建时关联论文"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        resp = client.post('/api/notes', json={
            'title': 'Note with Paper',
            'content': 'content',
            'paper_ids': [paper.id]
        })
        assert resp.status_code == 201
        data = resp.get_json()
        # to_dict(include_papers=True) 应包含关联的论文
        assert 'papers' in data['note']

    def test_create_note_duplicate_url(self, client, make_user, make_note):
        """URL 重复检测"""
        user = make_user(username='alice', password='alice12345')
        make_note(title='Original', content='c1', url='https://example.com/note',
                  user_id=user.id, is_public=True)

        resp = client.post('/api/notes', json={
            'title': 'Duplicate',
            'content': 'different content',
            'url': 'https://example.com/note'
        })
        assert resp.status_code == 409
        data = resp.get_json()
        assert data.get('duplicate') is True

    def test_create_note_duplicate_title(self, client, make_user, make_note):
        """标题相似度重复检测"""
        user = make_user(username='alice', password='alice12345')
        make_note(title='Machine Learning Basics',
                  content='c1', user_id=user.id, is_public=True)

        # 完全相同的标题应被识别为重复
        resp = client.post('/api/notes', json={
            'title': 'Machine Learning Basics',
            'content': 'different content here'
        })
        assert resp.status_code == 409


class TestNoteDetail:
    """笔记详情 API"""

    def test_get_note_detail(self, client, make_user, make_note):
        """获取详情"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Detail', content='content',
                         user_id=user.id, is_public=True)

        resp = client.get(f'/api/notes/{note.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['note']['id'] == note.id
        assert data['note']['title'] == 'Detail'

    def test_get_nonexistent_note(self, client):
        """不存在的笔记 404"""
        resp = client.get('/api/notes/99999')
        assert resp.status_code == 404


class TestNoteUpdate:
    """笔记更新 API"""

    def test_update_note_title(self, client, make_user, make_note):
        """更新标题"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Old', content='c',
                         user_id=user.id, is_public=True)

        resp = client.put(f'/api/notes/{note.id}', json={'title': 'New Title'})
        assert resp.status_code == 200
        assert resp.get_json()['note']['title'] == 'New Title'

    def test_update_note_content(self, client, make_user, make_note):
        """更新内容"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='old',
                         user_id=user.id, is_public=True)

        resp = client.put(f'/api/notes/{note.id}', json={'content': 'new content'})
        assert resp.status_code == 200

    def test_update_note_starred(self, client, make_user, make_note):
        """更新标星状态"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c', starred=False,
                         user_id=user.id, is_public=True)

        resp = client.put(f'/api/notes/{note.id}', json={'starred': True})
        assert resp.status_code == 200
        assert resp.get_json()['note']['starred'] is True

    def test_update_nonexistent_note(self, client):
        """更新不存在的笔记 404"""
        resp = client.put('/api/notes/99999', json={'title': 'x'})
        assert resp.status_code == 404


class TestNoteDelete:
    """笔记删除 API"""

    def test_delete_note(self, client, make_user, make_note):
        """删除笔记"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='To Delete', content='c',
                         user_id=user.id, is_public=True)

        resp = client.delete(f'/api/notes/{note.id}')
        assert resp.status_code == 200

        # 验证已删除
        resp2 = client.get(f'/api/notes/{note.id}')
        assert resp2.status_code == 404

    def test_delete_nonexistent_note(self, client):
        """删除不存在的笔记 404"""
        resp = client.delete('/api/notes/99999')
        assert resp.status_code == 404


class TestNotePaperAssociation:
    """笔记-论文关联 API"""

    def test_link_note_to_paper(self, client, make_user, make_note, make_paper):
        """关联笔记到论文"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        resp = client.post(f'/api/notes/{note.id}/papers',
                           json={'paper_id': paper.id})
        assert resp.status_code == 200

        # 验证关联
        resp2 = client.get(f'/api/notes/{note.id}/papers')
        assert resp2.status_code == 200
        papers = resp2.get_json()['papers']
        assert any(p['id'] == paper.id for p in papers)

    def test_unlink_note_from_paper(self, client, make_user, make_note, make_paper):
        """取消关联"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        # 先关联
        client.post(f'/api/notes/{note.id}/papers', json={'paper_id': paper.id})
        # 再取消
        resp = client.delete(f'/api/notes/{note.id}/papers/{paper.id}')
        assert resp.status_code == 200

    def test_link_to_nonexistent_paper(self, client, make_user, make_note):
        """关联不存在的论文 404"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)

        resp = client.post(f'/api/notes/{note.id}/papers',
                           json={'paper_id': 99999})
        assert resp.status_code == 404

    def test_link_without_paper_id(self, client, make_user, make_note):
        """缺少 paper_id 400"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)

        resp = client.post(f'/api/notes/{note.id}/papers', json={})
        assert resp.status_code == 400


class TestNoteTagAssociation:
    """笔记-标签关联 API"""

    def test_add_tag_to_note_by_name(self, client, make_user, make_note, make_tag):
        """通过名称添加标签"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)
        tag = make_tag(name='ml', user_id=user.id, is_public=True)

        resp = client.post(f'/api/notes/{note.id}/tags',
                           json={'name': 'ml'})
        assert resp.status_code == 200

        # 验证
        resp2 = client.get(f'/api/notes/{note.id}/tags')
        assert resp2.status_code == 200
        tag_names = [t['name'] for t in resp2.get_json()['tags']]
        assert 'ml' in tag_names

    def test_list_note_tags(self, client, make_user, make_note):
        """获取笔记标签列表"""
        user = make_user(username='alice', password='alice12345')
        note = make_note(title='Note', content='c',
                         user_id=user.id, is_public=True)

        resp = client.get(f'/api/notes/{note.id}/tags')
        assert resp.status_code == 200
        assert 'tags' in resp.get_json()
