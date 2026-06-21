"""
P2 迁移脚本测试

覆盖：
- 迁移脚本幂等性（可重复执行）
- 字段添加正确
- 数据回填正确
- user_paper_status 初始化

注：迁移脚本测试使用独立的内存数据库，不依赖 conftest 的 app fixture
"""
import pytest
import sys
from pathlib import Path
from sqlalchemy import create_engine, text, inspect

ROOT = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def fresh_engine(monkeypatch):
    """每个迁移测试独立的内存数据库

    通过 monkeypatch 替换 backend.config 的全局状态，
    让迁移脚本使用全新的内存数据库。
    """
    import backend.config as cfg

    # 重置全局状态
    monkeypatch.setattr(cfg, '_engine', None)
    monkeypatch.setattr(cfg, '_session_factory', None)
    monkeypatch.setattr(cfg, '_ScopedSession', None)
    monkeypatch.setattr(cfg.Config, 'SQLALCHEMY_DATABASE_URI', 'sqlite:///:memory:')

    # 重写 init_db：SQLite 内存数据库兼容
    def _test_init_db():
        from sqlalchemy.orm import sessionmaker, scoped_session
        if cfg._engine is None:
            cfg._engine = create_engine(
                'sqlite:///:memory:',
                echo=False,
                connect_args={'check_same_thread': False}
            )
            cfg._session_factory = sessionmaker(bind=cfg._engine, expire_on_commit=False)
            cfg._ScopedSession = scoped_session(cfg._session_factory)

    monkeypatch.setattr(cfg, 'init_db', _test_init_db)

    # 初始化
    cfg.init_db()
    engine = cfg.get_engine()

    yield engine

    # 清理
    if cfg._ScopedSession is not None:
        cfg._ScopedSession.remove()
    cfg._engine = None
    cfg._session_factory = None
    cfg._ScopedSession = None


class TestMigrationIdempotency:
    """迁移脚本幂等性测试"""

    def _run_migration(self):
        """执行迁移脚本"""
        import importlib.util

        # 重新导入迁移模块（避免缓存）
        for mod_name in list(sys.modules.keys()):
            if 'migrate_p2' in mod_name:
                del sys.modules[mod_name]

        # 用 importlib 直接加载文件，避免 scripts/ 不是包的问题
        spec = importlib.util.spec_from_file_location(
            'migrate_p2_add_user_fields',
            str(ROOT / 'scripts' / 'migrate_p2_add_user_fields.py')
        )
        migrate = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migrate)
        migrate.main()
        return migrate

    def test_run_migration_twice_no_error(self, fresh_engine):
        """迁移脚本执行两次不应报错"""
        try:
            migrate = self._run_migration()
            migrate.main()  # 第二次执行
        except Exception as e:
            pytest.fail(f"迁移脚本不幂等: {e}")

    def test_migration_adds_user_id_column(self, fresh_engine):
        """迁移后业务表应有 user_id 列

        测试逻辑：先创建"旧版"表结构（不含 user_id/is_public/created_by），
        再执行迁移，验证字段被正确添加。
        """
        # 先创建旧版表结构（模拟 P1 之前的数据库）
        old_schema_sql = """
        CREATE TABLE papers (
            id INTEGER PRIMARY KEY,
            title VARCHAR NOT NULL,
            source VARCHAR NOT NULL,
            starred BOOLEAN DEFAULT 0
        );
        CREATE TABLE articles (
            id INTEGER PRIMARY KEY,
            title VARCHAR(500) NOT NULL,
            source VARCHAR(50) NOT NULL
        );
        CREATE TABLE notes (
            id INTEGER PRIMARY KEY,
            content TEXT NOT NULL
        );
        CREATE TABLE tags (
            id INTEGER PRIMARY KEY,
            name VARCHAR NOT NULL,
            type VARCHAR NOT NULL DEFAULT 'custom'
        );
        CREATE TABLE wechat_subscriptions (
            id INTEGER PRIMARY KEY,
            account_name VARCHAR(200) NOT NULL
        );
        CREATE TABLE wechat_config (
            id INTEGER PRIMARY KEY,
            api_key VARCHAR(100)
        );
        """
        with fresh_engine.connect() as conn:
            for stmt in old_schema_sql.strip().split(';'):
                stmt = stmt.strip()
                if stmt:
                    conn.execute(text(stmt))
            conn.commit()

        # 执行迁移
        self._run_migration()

        inspector = inspect(fresh_engine)
        for table_name in ['papers', 'articles', 'notes', 'tags',
                          'wechat_subscriptions', 'wechat_config']:
            cols = {c['name'] for c in inspector.get_columns(table_name)}
            assert 'user_id' in cols, f"{table_name} 缺少 user_id"
            assert 'is_public' in cols, f"{table_name} 缺少 is_public"
            assert 'created_by' in cols, f"{table_name} 缺少 created_by"

    def test_migration_creates_user_paper_status_table(self, fresh_engine):
        """迁移后应存在 user_paper_status 表"""
        self._run_migration()

        inspector = inspect(fresh_engine)
        assert 'user_paper_status' in inspector.get_table_names()

    def test_migration_creates_default_admin(self, fresh_engine):
        """迁移后应存在至少一个 admin 用户"""
        self._run_migration()

        with fresh_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT COUNT(*) FROM users WHERE is_admin = 1"
            )).scalar()
            assert result >= 1, "应至少有一个管理员"

    def test_migration_backfills_existing_data(self, fresh_engine):
        """迁移应将现有数据归属 admin 并标记公共"""
        # 先创建表结构（通过 Base.metadata.create_all）
        from backend.models import Base
        Base.metadata.create_all(fresh_engine)

        # 插入"旧数据"——需要提供 is_public 因为模型定义了 NOT NULL
        with fresh_engine.connect() as conn:
            conn.execute(text(
                "INSERT INTO papers (title, source, is_public) "
                "VALUES ('Legacy Paper', 'manual', 0)"
            ))
            conn.commit()

        # 执行迁移
        self._run_migration()

        # 验证数据被回填
        with fresh_engine.connect() as conn:
            result = conn.execute(text(
                "SELECT user_id, is_public FROM papers WHERE title = 'Legacy Paper'"
            )).fetchone()
            assert result is not None
            assert result[0] is not None, "user_id 应被回填"
            assert result[1] == 1, "is_public 应为 True（1）"
