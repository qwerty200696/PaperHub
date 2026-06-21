"""
Articles API CRUD 集成测试

覆盖：
- GET    /api/articles               列表（含搜索/过滤）
- POST   /api/articles               创建（含重复检测）
- GET    /api/articles/<id>          详情
- PUT    /api/articles/<id>          更新
- DELETE /api/articles/<id>          删除
- POST   /api/articles/<id>/papers   关联论文
- DELETE /api/articles/<id>/papers/<pid>  取消关联
- POST   /api/articles/<id>/tags     添加标签
"""
import pytest


class TestArticlesList:
    """文章列表 API"""

    def test_list_articles_empty(self, client):
        """空数据库返回空列表"""
        resp = client.get('/api/articles')
        assert resp.status_code == 200
        data = resp.get_json()
        assert 'articles' in data
        assert isinstance(data['articles'], list)
        assert data['total'] == 0

    def test_list_articles_with_data(self, client, make_user, make_article):
        """有数据时返回文章列表"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='Article 1', user_id=user.id, is_public=True)
        make_article(title='Article 2', user_id=user.id, is_public=True)

        resp = client.get('/api/articles')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['total'] >= 2

    def test_list_articles_filter_by_source(self, client, make_user, make_article):
        """按来源过滤"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='Wechat', source='wechat',
                     user_id=user.id, is_public=True)
        make_article(title='Zhihu', source='zhihu',
                     user_id=user.id, is_public=True)

        resp = client.get('/api/articles?source=wechat')
        assert resp.status_code == 200
        data = resp.get_json()
        for a in data['articles']:
            assert a['source'] == 'wechat'

    def test_list_articles_keyword_search(self, client, make_user, make_article):
        """关键词搜索（标题/作者/内容）"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='Deep Learning Guide', author='Alice',
                     content='c', user_id=user.id, is_public=True)
        make_article(title='Other', author='Bob',
                     content='c', user_id=user.id, is_public=True)

        # 按标题搜索
        resp = client.get('/api/articles?search=Deep')
        assert resp.status_code == 200
        data = resp.get_json()
        assert any('Deep' in a['title'] for a in data['articles'])

    def test_list_articles_search_by_author(self, client, make_user, make_article):
        """按作者搜索"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='T1', author='Special Author',
                     content='c', user_id=user.id, is_public=True)

        resp = client.get('/api/articles?search=Special Author')
        assert resp.status_code == 200
        data = resp.get_json()
        assert any(a.get('author') == 'Special Author' for a in data['articles'])


class TestArticleCreate:
    """文章创建 API"""

    def test_create_article_basic(self, client):
        """基础创建"""
        resp = client.post('/api/articles', json={
            'title': 'New Article',
            'source': 'wechat',
            'content': 'article content',
            'author': 'Tester'
        })
        assert resp.status_code == 201
        data = resp.get_json()
        assert data['article']['title'] == 'New Article'

    def test_create_article_missing_title(self, client):
        """缺少标题 400"""
        resp = client.post('/api/articles', json={
            'source': 'wechat'
        })
        assert resp.status_code == 400

    def test_create_article_missing_source(self, client):
        """缺少来源 400"""
        resp = client.post('/api/articles', json={
            'title': 'No Source'
        })
        assert resp.status_code == 400

    def test_create_article_no_body(self, client):
        """无请求体 400"""
        resp = client.post('/api/articles')
        assert resp.status_code == 400

    def test_create_article_duplicate_url(self, client, make_user, make_article):
        """URL 重复检测"""
        user = make_user(username='alice', password='alice12345')
        make_article(title='Original', url='https://example.com/a',
                     user_id=user.id, is_public=True)

        resp = client.post('/api/articles', json={
            'title': 'Duplicate',
            'source': 'wechat',
            'url': 'https://example.com/a'
        })
        assert resp.status_code == 409
        assert resp.get_json().get('duplicate') is True


class TestArticleDetail:
    """文章详情 API"""

    def test_get_article_detail(self, client, make_user, make_article):
        """获取详情"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='Detail', user_id=user.id, is_public=True)

        resp = client.get(f'/api/articles/{article.id}')
        assert resp.status_code == 200
        data = resp.get_json()
        assert data['article']['id'] == article.id

    def test_get_nonexistent_article(self, client):
        """不存在的文章 404"""
        resp = client.get('/api/articles/99999')
        assert resp.status_code == 404


class TestArticleUpdate:
    """文章更新 API"""

    def test_update_article_title(self, client, make_user, make_article):
        """更新标题"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='Old', user_id=user.id, is_public=True)

        resp = client.put(f'/api/articles/{article.id}', json={'title': 'New'})
        assert resp.status_code == 200
        assert resp.get_json()['article']['title'] == 'New'

    def test_update_article_author(self, client, make_user, make_article):
        """更新作者"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)

        resp = client.put(f'/api/articles/{article.id}', json={'author': 'New Author'})
        assert resp.status_code == 200
        assert resp.get_json()['article']['author'] == 'New Author'

    def test_update_article_starred(self, client, make_user, make_article):
        """更新标星"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', starred=False,
                               user_id=user.id, is_public=True)

        resp = client.put(f'/api/articles/{article.id}', json={'starred': True})
        assert resp.status_code == 200
        assert resp.get_json()['article']['starred'] is True

    def test_update_nonexistent_article(self, client):
        """更新不存在 404"""
        resp = client.put('/api/articles/99999', json={'title': 'x'})
        assert resp.status_code == 404


class TestArticleDelete:
    """文章删除 API"""

    def test_delete_article(self, client, make_user, make_article):
        """删除文章"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='To Delete', user_id=user.id, is_public=True)

        resp = client.delete(f'/api/articles/{article.id}')
        assert resp.status_code == 200

        # 验证已删除
        resp2 = client.get(f'/api/articles/{article.id}')
        assert resp2.status_code == 404

    def test_delete_nonexistent_article(self, client):
        """删除不存在 404"""
        resp = client.delete('/api/articles/99999')
        assert resp.status_code == 404


class TestArticlePaperAssociation:
    """文章-论文关联 API"""

    def test_link_paper_to_article(self, client, make_user, make_article, make_paper):
        """关联论文到文章"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='Article', user_id=user.id, is_public=True)
        paper = make_paper(title='Paper', user_id=user.id, is_public=True)

        resp = client.post(f'/api/articles/{article.id}/papers',
                           json={'paper_id': paper.id})
        assert resp.status_code == 200

    def test_link_without_paper_id(self, client, make_user, make_article):
        """缺少 paper_id 400"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)

        resp = client.post(f'/api/articles/{article.id}/papers', json={})
        assert resp.status_code == 400

    def test_link_to_nonexistent_paper(self, client, make_user, make_article):
        """关联不存在的论文 404"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)

        resp = client.post(f'/api/articles/{article.id}/papers',
                           json={'paper_id': 99999})
        assert resp.status_code == 404

    def test_unlink_paper_from_article(self, client, make_user, make_article, make_paper):
        """取消关联"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)
        paper = make_paper(title='P', user_id=user.id, is_public=True)

        # 先关联
        client.post(f'/api/articles/{article.id}/papers',
                    json={'paper_id': paper.id})
        # 再取消
        resp = client.delete(f'/api/articles/{article.id}/papers/{paper.id}')
        assert resp.status_code == 200


class TestArticleTagAssociation:
    """文章-标签关联 API"""

    def test_add_tag_to_article(self, client, make_user, make_article, make_tag):
        """添加标签（通过 name）"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)
        tag = make_tag(name='test-tag', user_id=user.id, is_public=True)

        resp = client.post(f'/api/articles/{article.id}/tags',
                           json={'name': 'test-tag'})
        assert resp.status_code == 200

    def test_add_tag_without_name(self, client, make_user, make_article):
        """缺少标签名 400"""
        user = make_user(username='alice', password='alice12345')
        article = make_article(title='A', user_id=user.id, is_public=True)

        resp = client.post(f'/api/articles/{article.id}/tags',
                           json={'name': ''})
        assert resp.status_code == 400

    def test_add_tag_to_nonexistent_article(self, client):
        """添加到不存在的文章 404"""
        resp = client.post('/api/articles/99999/tags', json={'name': 'x'})
        assert resp.status_code == 404
