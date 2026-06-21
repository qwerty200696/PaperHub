"""
User Model - 用户模型（P1 阶段：多用户系统基础设施）
"""
from datetime import datetime

try:
    from backend.models import Base
except ImportError:
    try:
        from models import Base
    except ImportError:
        from sqlalchemy.ext.declarative import declarative_base
        Base = declarative_base()

from sqlalchemy import Column, Integer, String, Boolean, DateTime


class User(Base):
    """用户表

    P1 阶段仅建立表结构与认证能力，业务表的 user_id/is_public 字段在 P2 阶段添加。
    首个注册的用户自动成为管理员（is_admin=1）。
    """
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True, index=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_admin = Column(Boolean, default=False, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    # ── 密码哈希（bcrypt）─────────────────────────────
    def set_password(self, password):
        """设置密码（bcrypt 哈希）"""
        import bcrypt
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """校验密码"""
        import bcrypt
        try:
            return bcrypt.checkpw(
                password.encode('utf-8'),
                self.password_hash.encode('utf-8')
            )
        except (ValueError, AttributeError):
            return False

    # ── 序列化 ───────────────────────────────────────
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }
