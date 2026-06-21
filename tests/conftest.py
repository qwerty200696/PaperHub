"""
pytest 全局配置与 fixtures

核心设计：
1. 使用 SQLite 内存数据库（:memory:）做测试隔离，不污染生产数据
2. 通过 monkeypatch 重置 backend.config 的全局单例 engine/session
3. 每个测试函数独立事务，测试后回滚
4. 提供 app / client / db_session / auth_client 等通用 fixtures

使用方式：
    pytest tests/                    # 运行全部测试
    pytest tests/unit/               # 仅单元测试
    pytest tests/api/                # 仅 API 测试
    pytest tests/unit/test_user_model.py::test_password_hashing  # 单个测试
"""
import os
import sys
from pathlib import Path

import pytest

# ============================================================
# 路径设置：让测试能从项目根目录导入 backend
# 同时需要 backend/ 在路径中（因为部分 api/services 模块用短路径导入）
# 为避免 backend.models 和 models 被视为两个模块导致 Table 重复定义，
# 在导入后设置 sys.modules 别名
# ============================================================
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))

# 预导入 backend 模块并设置短路径别名，防止重复加载
import backend.config  # noqa: E402
import backend.models  # noqa: E402
import backend.models.paper  # noqa: E402
import backend.models.user  # noqa: E402
import backend.models.mixins  # noqa: E402

sys.modules.setdefault('config', sys.modules['backend.config'])
sys.modules.setdefault('models', sys.modules['backend.models'])
sys.modules.setdefault('models.paper', sys.modules['backend.models.paper'])
sys.modules.setdefault('models.user', sys.modules['backend.models.user'])
sys.modules.setdefault('models.mixins', sys.modules['backend.models.mixins'])

# 测试环境变量：使用固定的 JWT 密钥，避免环境差异
os.environ.setdefault('JWT_SECRET_KEY', 'test-jwt-secret-key-for-pytest-only')
os.environ.setdefault('SECRET_KEY', 'test-flask-secret-key-for-pytest-only')
os.environ.setdefault('ENFORCE_AUTH', '0')  # P1/P2 阶段不强制鉴权


# ============================================================
# 加速 bcrypt：测试环境使用最低 cost factor（4 而非默认 12）
# 生产环境 12 轮约 0.4s/次，测试 4 轮约 0.01s/次
# 这能让 50+ 个涉及密码哈希的测试从 ~20s 降到 ~0.5s
# ============================================================
import bcrypt as _bcrypt

_original_gensalt = _bcrypt.gensalt


def _fast_gensalt(rounds=12, prefix=b'2b'):
    """测试环境强制使用 rounds=4 加速"""
    return _original_gensalt(rounds=4, prefix=prefix)


_bcrypt.gensalt = _fast_gensalt


# ============================================================
# 核心 fixtures
# ============================================================
@pytest.fixture(scope='session')
def _reset_global_state():
    """重置 backend.config 的全局单例（session 级，仅执行一次）

    项目使用全局单例 engine/session_factory/scoped_session，
    测试启动时需要清空，让 init_db() 重新创建为内存数据库。

    SQLite 内存数据库不支持 pool_size/max_overflow/pool_timeout 参数，
    因此同时 monkeypatch init_db() 让它使用兼容参数。
    """
    import backend.config as cfg

    # 备份原值（便于恢复，虽然 session 结束后进程退出）
    original = {
        'engine': cfg._engine,
        'session_factory': cfg._session_factory,
        'ScopedSession': cfg._ScopedSession,
        'SQLALCHEMY_DATABASE_URI': cfg.Config.SQLALCHEMY_DATABASE_URI,
        'init_db': cfg.init_db,
    }

    # 强制使用内存数据库
    cfg._engine = None
    cfg._session_factory = None
    cfg._ScopedSession = None
    cfg.Config.SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # 重写 init_db：SQLite 内存数据库不支持连接池参数
    def _test_init_db():
        global _engine, _session_factory, _ScopedSession
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker, scoped_session
        if cfg._engine is None:
            cfg._engine = create_engine(
                'sqlite:///:memory:',
                echo=False,
                connect_args={'check_same_thread': False}
            )
            # expire_on_commit=False: commit 后对象不过期，避免 DetachedInstanceError
            cfg._session_factory = sessionmaker(
                bind=cfg._engine, expire_on_commit=False
            )
            cfg._ScopedSession = scoped_session(cfg._session_factory)

    cfg.init_db = _test_init_db

    yield cfg

    # 恢复（保险起见，避免影响后续 session）
    cfg._engine = original['engine']
    cfg._session_factory = original['session_factory']
    cfg._ScopedSession = original['ScopedSession']
    cfg.Config.SQLALCHEMY_DATABASE_URI = original['SQLALCHEMY_DATABASE_URI']
    cfg.init_db = original['init_db']


@pytest.fixture(scope='session')
def app(_reset_global_state):
    """创建 Flask 应用（session 级，所有测试共享一个 app 实例）

    使用内存数据库，所有表在创建时建立。
    """
    from backend.app import create_app

    flask_app = create_app('development')
    flask_app.config['TESTING'] = True
    flask_app.config['JWT_SECRET_KEY'] = 'test-jwt-secret-key-for-pytest-only'

    # 创建所有表
    from backend.models import Base
    from backend.config import get_engine
    Base.metadata.create_all(get_engine())

    yield flask_app


@pytest.fixture(scope='function')
def db_session(app):
    """每个测试函数独立的数据库 session

    通过清理所有表数据保证测试间数据隔离：
    - 测试开始：使用现有 session
    - 测试结束：回滚 + 删除所有表数据 + 清理 scoped_session
    """
    from backend.config import get_session, _ScopedSession, get_engine
    from backend.models import Base
    from sqlalchemy import text

    session = get_session()

    yield session

    # 清理：回滚未提交事务 + 删除所有表数据（保留表结构）
    session.rollback()
    session.close()

    engine = get_engine()
    with engine.connect() as conn:
        # SQLite: 禁用外键约束以便按任意顺序删除
        conn.execute(text("PRAGMA foreign_keys = OFF"))
        for table in reversed(Base.metadata.sorted_tables):
            conn.execute(table.delete())
        conn.execute(text("PRAGMA foreign_keys = ON"))
        conn.commit()

    if _ScopedSession is not None:
        _ScopedSession.remove()


@pytest.fixture(scope='function')
def client(app):
    """Flask 测试客户端"""
    return app.test_client()


@pytest.fixture(scope='function')
def app_context(app):
    """Flask 应用上下文（JWT 签发需要）"""
    with app.app_context():
        yield app


# ============================================================
# 用户相关 fixtures
# ============================================================
@pytest.fixture
def make_user(db_session):
    """创建用户的工厂 fixture

    用法：
        def test_xxx(make_user):
            user = make_user(username='alice', password='alice12345')
    """
    from backend.models import User

    def _make(username='testuser', password='testpass12345',
              is_admin=False, display_name=None, is_active=True):
        user = User(
            username=username,
            display_name=display_name or username,
            is_admin=is_admin,
            is_active=is_active,
        )
        user.set_password(password)
        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)
        return user

    return _make


@pytest.fixture
def admin_user(make_user):
    """预创建的管理员用户"""
    return make_user(username='admin', password='admin12345', is_admin=True,
                     display_name='管理员')


@pytest.fixture
def normal_user(make_user):
    """预创建的普通用户"""
    return make_user(username='alice', password='alice12345',
                     display_name='Alice')


@pytest.fixture
def second_user(make_user):
    """第二个普通用户（用于测试数据隔离）"""
    return make_user(username='bob', password='bob12345678',
                     display_name='Bob')


@pytest.fixture
def auth_headers(client):
    """登录并返回 Authorization 头的工厂

    用法：
        def test_xxx(client, auth_headers, admin_user):
            h = auth_headers('admin', 'admin12345')
            resp = client.get('/api/auth/me', headers=h)
    """
    def _login(username, password):
        resp = client.post('/api/auth/login',
                           json={'username': username, 'password': password})
        assert resp.status_code == 200, f"登录失败: {resp.get_json()}"
        token = resp.get_json()['token']
        return {'Authorization': f'Bearer {token}'}

    return _login


@pytest.fixture
def admin_client(client, admin_user, auth_headers):
    """带管理员鉴权的 client

    用法：
        def test_xxx(admin_client):
            resp = admin_client.get('/api/users')
    """
    # 由于 client 是函数级 fixture，无法直接修改其 headers
    # 这里返回一个带 admin token 的 headers 字典，配合 client 使用
    return auth_headers('admin', 'admin12345')


@pytest.fixture
def normal_client(client, normal_user, auth_headers):
    """带普通用户鉴权的 headers"""
    return auth_headers('alice', 'alice12345')


# ============================================================
# 业务数据 fixtures
# ============================================================
@pytest.fixture
def make_paper(db_session):
    """创建论文的工厂"""
    from backend.models import Paper

    def _make(title='Test Paper', user_id=None, is_public=False, **kwargs):
        paper = Paper(
            title=title,
            source=kwargs.get('source', 'manual'),
            user_id=user_id,
            is_public=is_public,
            **{k: v for k, v in kwargs.items() if k != 'source'}
        )
        db_session.add(paper)
        db_session.commit()
        db_session.refresh(paper)
        return paper

    return _make


@pytest.fixture
def make_tag(db_session):
    """创建标签的工厂"""
    from backend.models import Tag

    def _make(name='test-tag', user_id=None, is_public=False, **kwargs):
        tag = Tag(
            name=name,
            user_id=user_id,
            is_public=is_public,
            **kwargs
        )
        db_session.add(tag)
        db_session.commit()
        db_session.refresh(tag)
        return tag

    return _make


@pytest.fixture
def make_note(db_session):
    """创建笔记的工厂"""
    from backend.models import Note

    def _make(title='Test Note', content='note content',
              user_id=None, is_public=False, **kwargs):
        note = Note(
            title=title,
            content=content,
            user_id=user_id,
            is_public=is_public,
            **kwargs
        )
        db_session.add(note)
        db_session.commit()
        db_session.refresh(note)
        return note

    return _make


@pytest.fixture
def make_article(db_session):
    """创建文章的工厂"""
    from backend.models import Article

    def _make(title='Test Article', user_id=None, is_public=False, **kwargs):
        article = Article(
            title=title,
            source=kwargs.get('source', 'wechat'),
            user_id=user_id,
            is_public=is_public,
            **{k: v for k, v in kwargs.items() if k != 'source'}
        )
        db_session.add(article)
        db_session.commit()
        db_session.refresh(article)
        return article

    return _make
