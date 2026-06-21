# PaperHub 多用户隔离设计文档

> 版本：v1.0
> 日期：2026-06-21
> 状态：设计中

## 目录

1. [设计目标](#1-设计目标)
2. [整体架构](#2-整体架构)
3. [数据库设计](#3-数据库设计)
4. [认证系统设计（JWT）](#4-认证系统设计jwt)
5. [数据隔离策略](#5-数据隔离策略)
6. [公共数据策略](#6-公共数据策略)
7. [API 设计](#7-api-设计)
8. [数据迁移方案](#8-数据迁移方案)
9. [前端改造](#9-前端改造)
10. [实施阶段划分](#10-实施阶段划分)
11. [安全考虑](#11-安全考虑)
12. [风险与回滚](#12-风险与回滚)

---

## 1. 设计目标

### 1.1 业务目标

- 支持 1-5 人小团队共用一个 PaperHub 实例
- 每个用户有独立的论文/文章/笔记/标签视图
- 部分数据可标记为公共，供所有用户共享
- 现有单用户数据平滑迁移，不丢失

### 1.2 技术目标

- **隔离方案**：单库 + `user_id` 行级隔离（方案 A）
- **认证方式**：JWT Token（无状态）
- **向后兼容**：分阶段实施，P1 完成后现有 API 仍可无鉴权访问
- **运维友好**：不引入 Redis 等额外依赖（token 黑名单用内存 dict）

### 1.3 非目标

- 不做 SaaS 化多租户（不考虑 PostgreSQL schema 方案）
- 不做细粒度权限（如"用户 A 可读用户 B 的某篇论文"），仅区分私有/公共
- 不做 OAuth/SSO（后续可扩展）

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────┐
│                      前端 (Vue 3 CDN)                    │
│  login.html ─→ localStorage 存 JWT                       │
│  请求拦截器 ─→ Authorization: Bearer <token>             │
│  401 拦截 ─→ 跳转登录页                                  │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│                   Flask 后端                             │
│                                                          │
│  ┌──────────────────────────────────────────────────┐   │
│  │  JWT 中间件 (auth_required 装饰器)                │   │
│  │  - 解析 Authorization header                      │   │
│  │  - 验证签名 + 过期时间                             │   │
│  │  - 检查黑名单                                     │   │
│  │  - 注入 g.current_user                            │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│  ┌────────────────────────▼──────────────────────────┐   │
│  │  API 蓝图 (papers/articles/notes/...)             │   │
│  │  - 查询：Paper.visible_to(user)                   │   │
│  │  - 写入：paper.user_id = user.id                  │   │
│  └──────────────────────────────────────────────────┘   │
│                          │                               │
│  ┌────────────────────────▼──────────────────────────┐   │
│  │  SQLAlchemy ORM                                   │   │
│  │  UserOwnedMixin: visible_to() / owned_by()        │   │
│  └──────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────┘
                         │
┌────────────────────────▼────────────────────────────────┐
│              SQLite (data/db/paperhub.db)               │
│                                                          │
│  users          ← 新增                                   │
│  papers         ← + user_id, is_public                  │
│  articles       ← + user_id, is_public                  │
│  notes          ← + user_id, is_public                  │
│  tags           ← + user_id, is_public                  │
│  paper_tags     ← 不变（通过 paper 间接归属）            │
│  token_blacklist ← 新增（可选，用于主动登出）            │
└─────────────────────────────────────────────────────────┘
```

---

## 3. 数据库设计

### 3.1 新增表

#### `users` 表

```sql
CREATE TABLE users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,              -- bcrypt 哈希
    display_name  TEXT,
    is_admin      BOOLEAN NOT NULL DEFAULT 0,    -- 管理员可管理公共数据
    is_active     BOOLEAN NOT NULL DEFAULT 1,    -- 软禁用
    created_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_users_username ON users(username);
```

#### `token_blacklist` 表（可选，用于主动登出）

```sql
CREATE TABLE token_blacklist (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    jti         TEXT NOT NULL UNIQUE,            -- JWT ID
    user_id     INTEGER NOT NULL REFERENCES users(id),
    expires_at  TIMESTAMP NOT NULL,             -- 原 token 过期时间，过期后可清理
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_token_blacklist_jti ON token_blacklist(jti);
CREATE INDEX idx_token_blacklist_expires ON token_blacklist(expires_at);
```

### 3.2 业务表变更

以下表新增 `user_id` 和 `is_public` 字段：

| 表 | user_id 语义 | is_public 默认 | 说明 |
|----|-------------|---------------|------|
| `papers` | 论文归属用户 | 0（私有） | arXiv 抓取的可由管理员标记为公共 |
| `articles` | 文章归属用户 | 0（私有） | 同上 |
| `notes` | 笔记归属用户 | 0（私有） | 笔记默认私有 |
| `tags` | 标签归属用户 | 见下文 | tech/conference 默认公共，custom 默认私有 |

**迁移 SQL**：

```sql
-- papers
ALTER TABLE papers ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE papers ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_papers_user ON papers(user_id);
CREATE INDEX idx_papers_public ON papers(is_public);

-- articles
ALTER TABLE articles ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE articles ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_articles_user ON articles(user_id);
CREATE INDEX idx_articles_public ON articles(is_public);

-- notes
ALTER TABLE notes ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE notes ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_notes_user ON notes(user_id);
CREATE INDEX idx_notes_public ON notes(is_public);

-- tags
ALTER TABLE tags ADD COLUMN user_id INTEGER REFERENCES users(id);
ALTER TABLE tags ADD COLUMN is_public BOOLEAN NOT NULL DEFAULT 0;
CREATE INDEX idx_tags_user ON tags(user_id);
CREATE INDEX idx_tags_public ON tags(is_public);
```

### 3.3 关联表不变

`paper_tags` / `note_tags` / `article_tags` / `article_papers` / `note_papers` / `note_articles` **无需变更**——它们通过外键间接归属用户。查询时通过 JOIN 主表过滤即可。

### 3.4 SQLAlchemy 模型

```python
# backend/models/user.py
class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(50), nullable=False, unique=True)
    password_hash = Column(String(255), nullable=False)
    display_name = Column(String(100))
    is_admin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)

    def set_password(self, password):
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'), bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'display_name': self.display_name,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }
```

```python
# backend/models/mixins.py
from sqlalchemy import or_

class UserOwnedMixin:
    """为业务表提供用户归属与可见性查询"""
    user_id = None      # 子类需声明
    is_public = None    # 子类需声明

    @classmethod
    def visible_to(cls, session, user):
        """用户可见数据 = 自己的私有 + 所有公共"""
        return session.query(cls).filter(
            or_(
                cls.user_id == user.id,
                cls.is_public == True
            )
        )

    @classmethod
    def owned_by(cls, session, user):
        """用户拥有的数据（仅私有，不含公共）"""
        return session.query(cls).filter(cls.user_id == user.id)

    @classmethod
    def get_owned_or_404(cls, session, user, item_id):
        """获取用户拥有的某条数据，不存在则 404"""
        item = session.query(cls).filter(
            cls.id == item_id,
            cls.user_id == user.id
        ).first()
        if not item:
            abort(404)
        return item
```

---

## 4. 认证系统设计（JWT）

### 4.1 JWT 载荷

```json
{
  "sub": 1,                    // user_id
  "username": "alice",
  "is_admin": false,
  "jti": "uuid4-string",       // 唯一 ID，用于黑名单
  "iat": 1735603200,           // 签发时间
  "exp": 1735689600            // 过期时间（默认 24 小时）
}
```

### 4.2 配置

```python
# backend/config.py 新增
class Config:
    # JWT 配置
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = 24 * 3600    # 24 小时（秒）
    JWT_HEADER_NAME = 'Authorization'
    JWT_HEADER_TYPE = 'Bearer'
```

### 4.3 中间件实现

```python
# backend/api/auth.py
import jwt
import uuid
from functools import wraps
from flask import request, g, jsonify, current_app
from datetime import datetime, timedelta

def generate_token(user):
    """签发 JWT"""
    payload = {
        'sub': user.id,
        'username': user.username,
        'is_admin': user.is_admin,
        'jti': str(uuid.uuid4()),
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(
            seconds=current_app.config['JWT_ACCESS_TOKEN_EXPIRES']
        ),
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm='HS256')

def decode_token(token):
    """解码并验证 JWT"""
    try:
        return jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
    except jwt.ExpiredSignatureError:
        return None, 'token_expired'
    except jwt.InvalidTokenError:
        return None, 'invalid_token'

def is_token_blacklisted(jti):
    """检查 token 是否在黑名单（内存实现，重启后清空）"""
    from backend.app import _token_blacklist
    return jti in _token_blacklist

def auth_required(f):
    """要求登录的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': '未提供认证 token'}), 401
        token = auth_header[7:]
        payload, err = decode_token(token)
        if err:
            return jsonify({'error': 'token 无效或已过期', 'reason': err}), 401
        if is_token_blacklisted(payload['jti']):
            return jsonify({'error': 'token 已失效'}), 401
        # 注入当前用户
        from backend.config import get_session
        from backend.models.user import User
        session = get_session()
        user = session.query(User).filter_by(id=payload['sub'], is_active=True).first()
        if not user:
            return jsonify({'error': '用户不存在或已禁用'}), 401
        g.current_user = user
        g.token_jti = payload['jti']
        return f(*args, **kwargs)
    return decorated

def admin_required(f):
    """要求管理员的装饰器"""
    @wraps(f)
    def decorated(*args, **kwargs):
        if not getattr(g, 'current_user', None) or not g.current_user.is_admin:
            return jsonify({'error': '需要管理员权限'}), 403
        return f(*args, **kwargs)
    return decorated
```

### 4.4 认证 API

```
POST /api/auth/register    注册（首个用户自动成为 admin）
POST /api/auth/login       登录，返回 JWT
GET  /api/auth/me          获取当前用户信息
POST /api/auth/logout      登出（token 加入黑名单）
PUT  /api/users/:id        更新用户信息（管理员或本人）
GET  /api/users            用户列表（仅管理员）
```

**请求/响应示例**：

```http
POST /api/auth/login
Content-Type: application/json

{
  "username": "alice",
  "password": "secret123"
}
```

```http
HTTP/1.1 200 OK
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "user": {
    "id": 1,
    "username": "alice",
    "display_name": "Alice",
    "is_admin": true
  }
}
```

---

## 5. 数据隔离策略

### 5.1 查询规则

所有业务查询必须遵循：

```python
# 列表查询：可见 = 自己的私有 + 所有公共
items = Paper.visible_to(session, g.current_user).filter(...).all()

# 详情查询：可见才能查看
item = Paper.visible_to(session, g.current_user).filter_by(id=item_id).first()
if not item:
    abort(404)

# 写入：必须设置 user_id
paper = Paper(...)
paper.user_id = g.current_user.id
paper.is_public = False   # 默认私有
session.add(paper)
session.commit()

# 更新/删除：只有 owner 或 admin 可操作
if item.user_id != g.current_user.id and not g.current_user.is_admin:
    abort(403)
```

### 5.2 特殊场景

| 场景 | 处理 |
|------|------|
| 公共论文，用户 A 修改了状态 | **状态字段独立**：状态/标星不入 papers 表，改入 `user_paper_status` 关联表（见 5.3） |
| 公共标签，用户 A 删除 | 仅 admin 可删除公共标签；普通用户只能取消自己与该标签的关联 |
| 用户 A 导入了一篇公共论文已存在的 arXiv | 去重逻辑：若 `arxiv_id` 已存在且 `is_public=1`，则不重复导入，仅给当前用户建立关联 |
| 笔记关联公共论文 | 允许，笔记本身私有，关联关系私有 |

### 5.3 阅读状态独立化（重要）

当前 `papers.status` / `papers.starred` 是论文级字段。多用户后，**同一篇公共论文不同人状态不同**，需要拆分：

**新增 `user_paper_status` 表**：

```sql
CREATE TABLE user_paper_status (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id   INTEGER NOT NULL REFERENCES users(id),
    paper_id  INTEGER NOT NULL REFERENCES papers(id),
    status    TEXT DEFAULT 'pending',    -- pending/reading/done/mastered
    starred   BOOLEAN DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, paper_id)
);
CREATE INDEX idx_user_paper_status ON user_paper_status(user_id, paper_id);
```

> **注意**：这是 P3 阶段的改造，会破坏现有 `papers.status` 字段。迁移时将现有状态数据导入 admin 用户的 `user_paper_status`。

---

## 6. 公共数据策略

### 6.1 公共数据范围

| 数据 | 默认 is_public | 谁可标记为公共 |
|------|---------------|--------------|
| 预设标签（tech/conference） | 1 | - |
| 自定义标签 | 0 | owner 或 admin |
| arXiv 论文 | 0（导入者私有） | owner 或 admin |
| 微信/知乎文章 | 0 | owner 或 admin |
| 笔记 | 0 | owner 或 admin |
| 阅读状态/标星 | -（在 user_paper_status 表，天然私有） | - |

### 6.2 公共数据操作权限

```python
# 标记为公共
@admin_required  # 或 owner
def mark_public(item_id):
    item = Paper.get_owned_or_404(session, g.current_user, item_id)
    item.is_public = True
    session.commit()

# 取消公共（仅 admin）
@admin_required
def mark_private(item_id):
    item = session.query(Paper).get(item_id)
    item.is_public = False
    session.commit()
```

### 6.3 公共数据去重

导入时若发现公共库已有相同内容：

```python
def import_paper(user, paper_data):
    # 1. 先查公共库
    existing = session.query(Paper).filter(
        Paper.arxiv_id == paper_data['arxiv_id'],
        Paper.is_public == True
    ).first()
    if existing:
        # 不重复导入，直接返回已有的公共论文
        return existing
    # 2. 否则创建私有副本
    paper = Paper(**paper_data, user_id=user.id, is_public=False)
    session.add(paper)
    session.commit()
    return paper
```

---

## 7. API 设计

### 7.1 认证 API

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| POST | `/api/auth/register` | 无 | 注册（首个用户自动 admin） |
| POST | `/api/auth/login` | 无 | 登录，返回 JWT |
| GET | `/api/auth/me` | 登录 | 获取当前用户 |
| POST | `/api/auth/logout` | 登录 | 登出，token 加黑名单 |
| PUT | `/api/users/:id` | 本人/admin | 更新用户信息 |
| GET | `/api/users` | admin | 用户列表 |

### 7.2 业务 API 改造

所有现有业务 API 加 `@auth_required` 装饰器，查询改为 `visible_to`：

```python
# 改造前
@bp.route('/papers')
def list_papers():
    papers = session.query(Paper).all()
    return jsonify([p.to_dict() for p in papers])

# 改造后
@bp.route('/papers')
@auth_required
def list_papers():
    papers = Paper.visible_to(session, g.current_user).all()
    return jsonify([p.to_dict() for p in papers])
```

### 7.3 公共数据管理 API

| 方法 | 路径 | 鉴权 | 说明 |
|------|------|------|------|
| PUT | `/api/papers/:id/visibility` | owner/admin | 设置 is_public |
| PUT | `/api/articles/:id/visibility` | owner/admin | 同上 |
| PUT | `/api/notes/:id/visibility` | owner/admin | 同上 |
| PUT | `/api/tags/:id/visibility` | owner/admin | 同上 |

---

## 8. 数据迁移方案

### 8.1 迁移脚本

`scripts/migration/001_init_multiuser.py`：

```python
"""
多用户系统初始化迁移
- 创建 users 表
- 创建默认 admin 账户
- 业务表加 user_id / is_public 字段
- 现有数据归 admin 并标记为公共
- 创建 user_paper_status 表，导入现有状态
"""
import sqlite3
from pathlib import Path
import bcrypt

def migrate(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    # 1. 创建 users 表
    c.execute('''CREATE TABLE IF NOT EXISTS users (...)''')

    # 2. 创建默认 admin（密码同用户名，首次登录强制修改）
    admin_hash = bcrypt.hashpw(b'admin', bcrypt.gensalt()).decode()
    c.execute(
        'INSERT INTO users (username, password_hash, display_name, is_admin) '
        'VALUES (?, ?, ?, 1)',
        ('admin', admin_hash, '管理员')
    )
    admin_id = c.lastrowid

    # 3. 业务表加字段
    for table in ['papers', 'articles', 'notes']:
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN user_id INTEGER')
        except sqlite3.OperationalError:
            pass  # 字段已存在
        try:
            c.execute(f'ALTER TABLE {table} ADD COLUMN is_public BOOLEAN DEFAULT 0')
        except sqlite3.OperationalError:
            pass

    # 4. 现有数据归 admin + 公共
    for table in ['papers', 'articles', 'notes']:
        c.execute(f'UPDATE {table} SET user_id = ?, is_public = 1 WHERE user_id IS NULL',
                  (admin_id,))

    # 5. tags 特殊处理
    c.execute('UPDATE tags SET is_public = 1, user_id = NULL '
              'WHERE type IN ("tech", "conference")')
    c.execute('UPDATE tags SET user_id = ?, is_public = 0 '
              'WHERE type = "custom" AND user_id IS NULL', (admin_id,))

    # 6. 创建 user_paper_status 表
    c.execute('''CREATE TABLE IF NOT EXISTS user_paper_status (...)''')

    # 7. 导入现有 papers.status / papers.starred 到 admin 的状态表
    c.execute('''INSERT INTO user_paper_status (user_id, paper_id, status, starred)
                 SELECT ?, id, status, starred FROM papers''', (admin_id,))

    conn.commit()
    conn.close()
    print(f'迁移完成。默认账户: admin / admin（请尽快修改密码）')
```

### 8.2 迁移步骤

1. **停服**（避免迁移期间有写入）
2. **备份数据库**：`cp data/db/paperhub.db data/db/paperhub.db.bak.$(date +%Y%m%d)`
3. **执行迁移**：`python scripts/migration/001_init_multiuser.py`
4. **启动服务**，用 admin/admin 登录
5. **立即修改 admin 密码**

---

## 9. 前端改造

### 9.1 新增页面

- `frontend/login.html`：登录/注册页
- `frontend/profile.html`：用户信息页（修改密码、display_name）

### 9.2 请求拦截器

```javascript
// frontend/src/modules/auth.js
const TOKEN_KEY = 'paperhub_token';

export function getToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export function isLoggedIn() {
  return !!getToken();
}

// fetch 封装：自动注入 token + 401 拦截
export async function api(url, options = {}) {
  const token = getToken();
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }
  const resp = await fetch(url, { ...options, headers });
  if (resp.status === 401) {
    clearToken();
    location.href = '/login.html';
    throw new Error('未登录或登录已过期');
  }
  return resp;
}
```

### 9.3 路由守卫

所有业务页面在加载时检查登录状态：

```javascript
// app.html / toolbox.html 等页面头部
if (!isLoggedIn()) {
  location.href = '/login.html';
}
```

---

## 10. 实施阶段划分

### P1：认证基础设施（不破坏现有功能）

**目标**：加 users 表、登录 API、JWT 中间件，但**不强制**现有 API 鉴权。

| 任务 | 文件 |
|------|------|
| 新增 User 模型 | `backend/models/user.py` |
| 新增 auth 蓝图 | `backend/api/auth.py` |
| 新增 JWT 中间件 | `backend/api/auth.py` |
| 新增依赖 bcrypt + PyJWT | `backend/requirements-py11.txt` |
| 注册 auth 蓝图 | `backend/app.py` |
| 初始化 users 表 | `backend/app.py` 的 `init_database()` |

**验收**：
- 可注册/登录，拿到 JWT
- `/api/auth/me` 可用
- 现有所有 API 仍可无鉴权访问（向后兼容）

### P2：表结构迁移 + 数据归属

**目标**：业务表加字段，现有数据归 admin + 公共。

| 任务 | 文件 |
|------|------|
| 迁移脚本 | `scripts/migration/001_init_multiuser.py` |
| 模型加 user_id / is_public 字段 | `backend/models/paper.py` |
| UserOwnedMixin | `backend/models/mixins.py` |

**验收**：
- 迁移后现有数据可正常访问
- admin/admin 可登录
- 字段已加但查询未强制过滤（仍向后兼容）

### P3：API 鉴权 + 隔离（破坏性变更）

**目标**：所有业务 API 加 `@auth_required`，查询用 `visible_to`。

| 任务 | 文件 |
|------|------|
| 改造 papers API | `backend/api/papers.py` |
| 改造 articles API | `backend/api/articles.py` |
| 改造 notes API | `backend/api/notes.py` |
| 改造 ingest API | `backend/api/ingest.py` |
| 改造 search API | `backend/api/search.py` |
| 改造 ai/backup/export 等 | 对应文件 |
| 新增 user_paper_status 表 | `backend/models/paper.py` |
| 状态/标星逻辑迁移 | 各 API |

**验收**：
- 未登录访问业务 API 返回 401
- 用户 A 看不到用户 B 的私有数据
- 公共数据所有人可见
- 同一篇公共论文不同用户状态独立

### P4：前端登录流程

**目标**：登录页、请求拦截器、401 跳转。

| 任务 | 文件 |
|------|------|
| 登录/注册页 | `frontend/login.html` |
| auth 模块 | `frontend/src/modules/auth.js` |
| 各页面路由守卫 | `frontend/app.html` 等 |
| 用户信息页 | `frontend/profile.html` |

### P5：公共数据管理 UI

**目标**：管理员可标记数据公共/私有。

| 任务 | 文件 |
|------|------|
| 论文/文章/笔记详情页加"设为公共"按钮 | 对应前端 |
| 标签管理页加公共标记 | 标签管理 UI |
| 用户管理页（admin） | `frontend/admin.html` |

---

## 11. 安全考虑

### 11.1 密码安全

- 使用 bcrypt 哈希（cost factor 默认 12）
- 密码最短 8 位
- 不存储明文密码

### 11.2 JWT 安全

- `JWT_SECRET_KEY` 必须与 `SECRET_KEY` 不同，生产环境通过环境变量注入
- token 默认 24 小时过期
- 登出加入黑名单（内存 dict，重启清空——可接受，因为重启后旧 token 仍有效但用户需重新登录）
- **不**在 localStorage 存敏感信息（仅存 token）

### 11.3 XSS 防护

- 前端所有用户输入渲染时转义（Vue 默认转义 `{{ }}`）
- 笔记内容用 `v-html` 渲染前需 DOMPurify 清洗
- CSP 头部限制脚本来源

### 11.4 越权防护

- 所有查询走 `visible_to` / `owned_by`，**禁止**裸 `query.filter_by(id=...)`
- 更新/删除操作检查 `user_id == current_user.id or is_admin`
- Code Review 重点检查：是否有 API 遗漏 `@auth_required`

### 11.5 暴力破解防护

- 登录接口限流：同 IP 5 次/分钟
- 失败 5 次锁定账户 15 分钟（可选，P3 阶段加）

---

## 12. 风险与回滚

### 12.1 风险

| 风险 | 影响 | 缓解 |
|------|------|------|
| P3 改造遗漏某 API 的 user_id 过滤 | 数据泄露 | Code Review + 自动化测试（用 A 账户创建数据，B 账户尝试访问应 404） |
| 迁移脚本执行失败 | 数据丢失 | 迁移前强制备份；脚本事务化 |
| 现有用户无 token，升级后无法访问 | 体验中断 | P1/P2 不强制鉴权，给用户缓冲期；P3 上线前公告 |
| token 黑名单重启丢失 | 登出失效 | 可接受；如需持久化可改用 SQLite 表 |

### 12.2 回滚方案

每个阶段独立可回滚：

- **P1 回滚**：删除 users 表 + auth 蓝图，无影响
- **P2 回滚**：恢复数据库备份（字段加了不用无影响，可不回滚）
- **P3 回滚**：恢复数据库备份 + 代码回退到 P2 状态
- **P4/P5 回滚**：前端回退，后端无影响

### 12.3 灰度策略

P3 上线时，可临时加一个开关：

```python
# backend/config.py
ENFORCE_AUTH = os.environ.get('ENFORCE_AUTH', '0') == '1'  # 默认不强制

# 中间件
def auth_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not current_app.config['ENFORCE_AUTH']:
            # 不强制时，尝试解析 token 但不报错
            ...
        else:
            # 强制时，无 token 报 401
            ...
```

灰度流程：
1. P3 上线，`ENFORCE_AUTH=0`，用户可逐步登录
2. 观察一周，确认无问题
3. 设置 `ENFORCE_AUTH=1`，强制鉴权

---

## 附录

### A. 新增依赖

```
# backend/requirements-py11.txt 追加
PyJWT==2.8.0
bcrypt==4.1.2
```

### B. 环境变量

```bash
# .env 新增
JWT_SECRET_KEY=your-jwt-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=86400   # 24h
ENFORCE_AUTH=0                   # 灰度开关
```

### C. 相关文件清单

| 文件 | 操作 | 阶段 |
|------|------|------|
| `backend/models/user.py` | 新增 | P1 |
| `backend/models/mixins.py` | 新增 | P2 |
| `backend/models/paper.py` | 修改（加字段） | P2 |
| `backend/api/auth.py` | 新增 | P1 |
| `backend/api/papers.py` | 修改（加鉴权） | P3 |
| `backend/api/articles.py` | 修改 | P3 |
| `backend/api/notes.py` | 修改 | P3 |
| `backend/api/ingest.py` | 修改 | P3 |
| `backend/api/search.py` | 修改 | P3 |
| `backend/api/ai.py` | 修改 | P3 |
| `backend/api/backup.py` | 修改 | P3 |
| `backend/api/export.py` | 修改 | P3 |
| `backend/app.py` | 修改（注册蓝图） | P1 |
| `backend/config.py` | 修改（加 JWT 配置） | P1 |
| `backend/requirements-py11.txt` | 修改 | P1 |
| `scripts/migration/001_init_multiuser.py` | 新增 | P2 |
| `frontend/login.html` | 新增 | P4 |
| `frontend/src/modules/auth.js` | 新增 | P4 |
| `frontend/app.html` | 修改（加守卫） | P4 |
