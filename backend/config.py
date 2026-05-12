"""
Configuration - 配置文件
"""
import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session

# 项目根目录 - 确保始终指向 PaperHub（兼容大小写）
def get_base_dir():
    current = Path(__file__).resolve()
    while current.name.lower() != 'paperhub':
        current = current.parent
        if current.parent == current:
            raise Exception("找不到 PaperHub 目录")
    return current

BASE_DIR = get_base_dir()

# 数据目录
DATA_DIR = BASE_DIR / 'data'
PAPERS_DIR = DATA_DIR / 'papers'
DB_DIR = DATA_DIR / 'db'
VECTORS_DIR = DATA_DIR / 'vectors'
BACKUPS_DIR = DATA_DIR / 'backups'
NOTE_IMAGES_DIR = PAPERS_DIR / 'note_images'

# 确保目录存在
for dir_path in [PAPERS_DIR, DB_DIR, VECTORS_DIR, BACKUPS_DIR,
                 PAPERS_DIR / 'arxiv', PAPERS_DIR / 'conference', PAPERS_DIR / 'others',
                 NOTE_IMAGES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # 数据库配置 - SQLite
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{DB_DIR / "paperhub.db"}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False

    # CORS 配置
    CORS_ORIGINS = ['http://localhost:5000', 'http://127.0.0.1:5000',
                    'http://localhost:5799', 'http://127.0.0.1:5799']

    # 文件上传配置
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024
    UPLOAD_FOLDER = PAPERS_DIR

    # ChromaDB 配置
    CHROMA_PERSIST_DIR = str(VECTORS_DIR / 'chroma')
    CHROMA_COLLECTION_NAME = 'papers'


class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False


config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

# ==========================================
# 全局 SQLAlchemy Engine 和 SessionFactory
# ==========================================

# 全局唯一的 Engine 实例（单例）
_engine = None
_session_factory = None
_ScopedSession = None

def init_db():
    """初始化全局数据库连接池和会话工厂
    应该在应用启动时调用一次
    """
    global _engine, _session_factory, _ScopedSession
    if _engine is None:
        # 创建 Engine，使用连接池
        _engine = create_engine(
            Config.SQLALCHEMY_DATABASE_URI,
            pool_size=5,              # 连接池大小
            max_overflow=10,         # 最大溢出连接数
            pool_timeout=30,          # 获取连接超时时间（秒）
            pool_recycle=3600,        # 连接回收时间（秒），避免 SQLite 锁问题
            echo=Config.SQLALCHEMY_ECHO
        )
        # 创建 Session工厂
        _session_factory = sessionmaker(bind=_engine)
        # 创建线程安全的 ScopedSession
        _ScopedSession = scoped_session(_session_factory)

def get_engine():
    """获取全局 Engine 实例"""
    if _engine is None:
        init_db()
    return _engine

def get_session():
    """获取一个新的 Session 实例
    每次调用者需要负责关闭这个 Session 的生命周期
    """
    if _ScopedSession is None:
        init_db()
    return _ScopedSession()

def get_scoped_session():
    """获取线程安全的 ScopedSession
    同一线程内多次调用返回同一个 Session
    使用完毕后需要调用 remove() 清理
    """
    if _ScopedSession is None:
        init_db()
    return _ScopedSession

def close_scoped_session(response_or_exc=None):
    """关闭当前线程的 ScopedSession
    应该在请求结束时调用
    """
    if _ScopedSession is not None:
        _ScopedSession.remove()
