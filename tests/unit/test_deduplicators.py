"""
服务层去重逻辑单元测试

覆盖：
- note_deduplicator: 标题标准化/相似度/编辑距离/URL 匹配/内容哈希
- article_deduplicator: 系列标识检测/标题标准化
"""
import pytest


class TestNoteDeduplicatorNormalize:
    """笔记去重 - 标题标准化"""

    def test_normalize_title_basic(self):
        from backend.services.note_deduplicator import normalize_title
        assert normalize_title('Hello World') == 'hello world'

    def test_normalize_title_punctuation(self):
        from backend.services.note_deduplicator import normalize_title
        # 标点应被移除
        assert normalize_title('Hello, World!') == 'hello world'

    def test_normalize_title_chinese(self):
        from backend.services.note_deduplicator import normalize_title
        # 中文应保留
        assert normalize_title('机器学习 基础') == '机器学习 基础'

    def test_normalize_title_whitespace(self):
        from backend.services.note_deduplicator import normalize_title
        assert normalize_title('Hello   World') == 'hello world'

    def test_normalize_title_empty(self):
        from backend.services.note_deduplicator import normalize_title
        assert normalize_title('') == ''
        assert normalize_title(None) == ''


class TestNoteDeduplicatorLevenshtein:
    """笔记去重 - 编辑距离"""

    def test_levenshtein_same(self):
        from backend.services.note_deduplicator import levenshtein_distance
        assert levenshtein_distance('abc', 'abc') == 0

    def test_levenshtein_different(self):
        from backend.services.note_deduplicator import levenshtein_distance
        assert levenshtein_distance('abc', 'xyz') == 3

    def test_levenshtein_insertion(self):
        from backend.services.note_deduplicator import levenshtein_distance
        assert levenshtein_distance('abc', 'abcd') == 1

    def test_levenshtein_empty(self):
        from backend.services.note_deduplicator import levenshtein_distance
        assert levenshtein_distance('', 'abc') == 3
        assert levenshtein_distance('abc', '') == 3
        assert levenshtein_distance('', '') == 0


class TestNoteDeduplicatorSimilarity:
    """笔记去重 - 标题相似度"""

    def test_similarity_identical(self):
        from backend.services.note_deduplicator import title_similarity
        assert title_similarity('Hello World', 'Hello World') == 1.0

    def test_similarity_completely_different(self):
        from backend.services.note_deduplicator import title_similarity
        sim = title_similarity('abc', 'xyz')
        assert 0.0 <= sim < 0.3

    def test_similarity_high(self):
        from backend.services.note_deduplicator import title_similarity
        # 仅差一个字符
        sim = title_similarity('Machine Learning', 'Machine Learning Basics')
        assert sim >= 0.6

    def test_similarity_empty(self):
        from backend.services.note_deduplicator import title_similarity
        assert title_similarity('', 'abc') == 0.0
        assert title_similarity('abc', '') == 0.0


class TestNoteDeduplicatorContentHash:
    """笔记去重 - 内容哈希"""

    def test_content_hash_same(self):
        from backend.services.note_deduplicator import content_hash
        assert content_hash('hello world') == content_hash('hello world')

    def test_content_hash_different(self):
        from backend.services.note_deduplicator import content_hash
        assert content_hash('hello') != content_hash('world')

    def test_content_hash_whitespace_normalized(self):
        from backend.services.note_deduplicator import content_hash
        # 多余空格应被规范化
        assert content_hash('hello  world') == content_hash('hello world')

    def test_content_hash_case_insensitive(self):
        from backend.services.note_deduplicator import content_hash
        assert content_hash('Hello') == content_hash('hello')

    def test_content_hash_empty(self):
        from backend.services.note_deduplicator import content_hash
        assert content_hash('') == ''
        assert content_hash(None) == ''


class TestCheckNoteDuplicate:
    """笔记去重 - check_note_duplicate 集成"""

    def test_duplicate_by_url(self, db_session, make_note):
        """URL 完全匹配"""
        make_note(title='A', content='c1', url='https://example.com/n1')
        from backend.services.note_deduplicator import check_note_duplicate
        from backend.models import Note

        result = check_note_duplicate(
            db_session, Note,
            title='Different Title',
            content='different',
            url='https://example.com/n1'
        )
        assert result is not None
        assert result.title == 'A'

    def test_duplicate_by_title(self, db_session, make_note):
        """标题完全匹配"""
        make_note(title='Machine Learning', content='c1')
        from backend.services.note_deduplicator import check_note_duplicate
        from backend.models import Note

        result = check_note_duplicate(
            db_session, Note,
            title='Machine Learning',
            content='different content'
        )
        assert result is not None

    def test_duplicate_by_content(self, db_session, make_note):
        """内容前 500 字符匹配"""
        content = 'a' * 300
        make_note(title='A', content=content)
        from backend.services.note_deduplicator import check_note_duplicate
        from backend.models import Note

        result = check_note_duplicate(
            db_session, Note,
            title='Different',
            content=content
        )
        assert result is not None

    def test_no_duplicate(self, db_session, make_note):
        """无重复"""
        make_note(title='A', content='content a', url='https://a.com')
        from backend.services.note_deduplicator import check_note_duplicate
        from backend.models import Note

        result = check_note_duplicate(
            db_session, Note,
            title='Completely Different',
            content='totally different content',
            url='https://different.com'
        )
        assert result is None


class TestArticleDeduplicator:
    """文章去重 - 系列标识"""

    def test_has_series_identifier_upper(self):
        from backend.services.article_deduplicator import has_series_identifier
        assert has_series_identifier('文章标题（上）') is True

    def test_has_series_identifier_lower(self):
        from backend.services.article_deduplicator import has_series_identifier
        assert has_series_identifier('文章标题（下）') is True

    def test_has_series_identifier_part(self):
        from backend.services.article_deduplicator import has_series_identifier
        assert has_series_identifier('系列（第一部分）') is True

    def test_has_series_identifier_number(self):
        from backend.services.article_deduplicator import has_series_identifier
        assert has_series_identifier('标题_1') is True
        assert has_series_identifier('标题 2') is True

    def test_no_series_identifier(self):
        from backend.services.article_deduplicator import has_series_identifier
        assert has_series_identifier('普通文章标题') is False
        assert has_series_identifier('Machine Learning') is False

    def test_normalize_title_keeps_series(self):
        """标准化标题应保留系列标识"""
        from backend.services.article_deduplicator import normalize_title
        # 系列标识应保留
        result = normalize_title('文章（上）')
        assert '上' in result

    def test_normalize_title_basic(self):
        from backend.services.article_deduplicator import normalize_title
        assert normalize_title('Hello World') == 'hello world'

    def test_normalize_title_chinese(self):
        from backend.services.article_deduplicator import normalize_title
        # 中文应保留
        assert '机器学习' in normalize_title('机器学习入门')


class TestArticleCheckDuplicate:
    """文章去重 - check_article_duplicate 集成"""

    def test_duplicate_by_url(self, db_session, make_article):
        """URL 完全匹配"""
        make_article(title='A', url='https://example.com/a1')
        from backend.services.article_deduplicator import check_article_duplicate
        from backend.models import Article

        result = check_article_duplicate(
            db_session, Article,
            title='Different',
            content='different',
            url='https://example.com/a1'
        )
        assert result is not None

    def test_no_duplicate(self, db_session, make_article):
        """无重复"""
        make_article(title='A', content='c1', url='https://a.com')
        from backend.services.article_deduplicator import check_article_duplicate
        from backend.models import Article

        result = check_article_duplicate(
            db_session, Article,
            title='Completely Different',
            content='totally different',
            url='https://different.com'
        )
        assert result is None
