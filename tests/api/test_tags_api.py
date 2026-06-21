"""
Tags API 集成测试

覆盖：
- GET    /api/tags                 标签列表（含论文计数）
- GET    /api/tags/articles        文章标签列表
- GET    /api/tags/notes           笔记标签列表
- POST   /api/papers/<id>/tags     给论文添加标签
- DELETE /api/papers/<id>/tags/<tid>  移除论文标签
"""
import pytest


class TestTagsList:
    """标签列表 API"""

    def test_list_tags_empty(self, client):
        """空数据库返回空列表或默认标签"""
        resp = client.get('/api/tags')
        assert resp.status_code == 200
        data = resp.get_json()
        # tags 可能是 list 或 dict
        tags = data if isinstance(data, list) else data.get('tags', [])
        assert isinstance(tags, list)

    def test_list_tags_with_data(self, client, make_user, make_tag):
        """有数据时返回标签列表"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='machine-learning', user_id=user.id, is_public=True)
        make_tag(name='physics', user_id=user.id, is_public=True)

        resp = client.get('/api/tags')
        assert resp.status_code == 200
        data = resp.get_json()
        tags = data if isinstance(data, list) else data.get('tags', [])
        names = [t['name'] for t in tags]
        assert 'machine-learning' in names
        assert 'physics' in names

    def test_tags_include_count_field(self, client, make_user, make_tag, make_paper, db_session):
        """标签列表应包含 count 字段（关联论文数）"""
        user = make_user(username='alice', password='alice12345')
        tag = make_tag(name='ml', user_id=user.id, is_public=True)
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)
        paper.tags.append(tag)
        db_session.commit()

        resp = client.get('/api/tags')
        assert resp.status_code == 200
        data = resp.get_json()
        tags = data if isinstance(data, list) else data.get('tags', [])
        ml_tag = next((t for t in tags if t['name'] == 'ml'), None)
        assert ml_tag is not None
        assert ml_tag.get('count', 0) >= 1

    def test_tags_include_owner_fields(self, client, make_user, make_tag):
        """标签应包含归属字段"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='test', user_id=user.id, is_public=True)

        resp = client.get('/api/tags')
        assert resp.status_code == 200
        data = resp.get_json()
        tags = data if isinstance(data, list) else data.get('tags', [])
        for t in tags:
            assert 'user_id' in t
            assert 'is_public' in t


class TestArticleTags:
    """文章标签 API"""

    def test_list_article_tags(self, client, make_user, make_tag):
        """获取文章标签列表"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='art-tag-1', user_id=user.id, is_public=True)
        make_tag(name='art-tag-2', user_id=user.id, is_public=True)

        resp = client.get('/api/tags/articles')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tags' in data
        names = [t['name'] for t in data['tags']]
        assert 'art-tag-1' in names


class TestNoteTags:
    """笔记标签 API"""

    def test_list_note_tags(self, client, make_user, make_tag):
        """获取笔记标签列表"""
        user = make_user(username='alice', password='alice12345')
        make_tag(name='note-tag', user_id=user.id, is_public=True)

        resp = client.get('/api/tags/notes')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'tags' in data
        names = [t['name'] for t in data['tags']]
        assert 'note-tag' in names


class TestPaperTagAssociation:
    """论文-标签关联 API"""

    def test_add_tag_to_paper_by_name(self, client, make_user, make_paper):
        """通过名称给论文添加标签（标签不存在时自动创建）"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        resp = client.post(f'/api/papers/{paper.id}/tags',
                           json={'name': 'new-tag'})
        assert resp.status_code == 200

    def test_add_existing_tag_to_paper(self, client, make_user, make_paper, make_tag):
        """添加已存在的标签到论文"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)
        make_tag(name='existing', user_id=user.id, is_public=True)

        resp = client.post(f'/api/papers/{paper.id}/tags',
                           json={'name': 'existing'})
        assert resp.status_code == 200

    def test_add_tag_without_name(self, client, make_user, make_paper):
        """缺少标签名 404"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        resp = client.post(f'/api/papers/{paper.id}/tags', json={'name': ''})
        assert resp.status_code == 404

    def test_add_tag_to_nonexistent_paper(self, client):
        """给不存在的论文添加标签 404"""
        resp = client.post('/api/papers/99999/tags', json={'name': 'x'})
        assert resp.status_code == 404

    def test_remove_tag_from_paper(self, client, make_user, make_paper, make_tag, db_session):
        """移除论文的标签"""
        user = make_user(username='alice', password='alice12345')
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)
        tag = make_tag(name='to-remove', user_id=user.id, is_public=True)
        paper.tags.append(tag)
        db_session.commit()

        resp = client.delete(f'/api/papers/{paper.id}/tags/{tag.id}')
        assert resp.status_code == 200

    def test_remove_tag_from_nonexistent_paper(self, client, make_tag):
        """从不存在的论文移除标签 404"""
        resp = client.delete('/api/papers/99999/tags/1')
        assert resp.status_code == 404
