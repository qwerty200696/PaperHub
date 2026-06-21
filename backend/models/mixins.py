"""
Model Mixins - 模型混入

UserOwnedMixin：封装多用户数据隔离的通用字段与方法
"""
from datetime import datetime

from sqlalchemy import Column, Integer, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship


class UserOwnedMixin:
    """用户归属混入

    为业务表提供：
    - user_id：归属用户（外键 -> users.id）
    - is_public：是否公共数据（公共数据所有用户可见）
    - created_by：创建者（与 user_id 通常一致，迁移场景下可能不同）

    通用方法：
    - visible_to(user): 该记录对指定用户是否可见
    - owned_by(user):   该记录是否归属指定用户
    """
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True, index=True)
    is_public = Column(Boolean, default=False, nullable=False, index=True)
    created_by = Column(Integer, ForeignKey('users.id'), nullable=True)

    def visible_to(self, user):
        """记录对 user 是否可见

        可见条件：
        1. 是公共数据（is_public=True）
        2. 归属该用户（user_id == user.id）
        3. 用户是管理员（管理员可见所有数据）
        """
        if user is None:
            return bool(self.is_public)
        if getattr(user, 'is_admin', False):
            return True
        if self.is_public:
            return True
        return self.user_id == user.id

    def owned_by(self, user):
        """记录是否归属 user（仅 owner 可修改/删除）"""
        if user is None:
            return False
        if getattr(user, 'is_admin', False):
            return True
        return self.user_id == user.id

    def to_dict_with_owner(self, base_dict):
        """将归属信息合并到 to_dict 输出"""
        base_dict['user_id'] = self.user_id
        base_dict['is_public'] = self.is_public
        return base_dict


class TimestampMixin:
    """时间戳混入（备用，目前业务表已各自定义）"""
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
