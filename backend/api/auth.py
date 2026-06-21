"""
Auth API - 认证与用户管理 API（P1 阶段）

提供：
- POST /api/auth/register  注册（首个用户自动成为管理员）
- POST /api/auth/login     登录，返回 JWT
- GET  /api/auth/me        获取当前用户信息
- POST /api/auth/logout    登出（token 加入黑名单）
- GET  /api/users          用户列表（仅管理员）
- PUT  /api/users/<id>     更新用户信息（本人或管理员）

JWT 中间件：
- auth_required  要求登录
- admin_required 要求管理员
- get_current_user  尝试解析 token，不报错（用于 P1 灰度阶段）

P1 阶段不强制鉴权，业务 API 仍可无 token 访问。
P3 阶段会在业务 API 上加 @auth_required 装饰器。
"""
import uuid
from datetime import datetime, timedelta
from functools import wraps

import jwt
from flask import Blueprint, request, g, jsonify, current_app

bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# 用户路由也挂在本蓝图下，统一前缀 /api
users_bp = Blueprint('users', __name__, url_prefix='/api/users')


# ============================================================
# Session / Model 工具
# ============================================================
def _get_session():
    try:
        from backend.config import get_session as _gs
    except ImportError:
        from config import get_session as _gs
    return _gs()


def _get_user_model():
    try:
        from backend.models.user import User
    except ImportError:
        from models.user import User
    return User


# ============================================================
# JWT 工具
# ============================================================
# 内存级 token 黑名单：{ jti: expires_at }
# 进程重启后清空——可接受，重启后旧 token 仍有效但用户需重新登录
_token_blacklist = {}


def generate_token(user):
    """签发 JWT

    载荷字段：
    - sub: user_id
    - username
    - is_admin
    - jti: 唯一 ID（用于黑名单）
    - iat / exp
    """
    now = datetime.utcnow()
    expires_delta = timedelta(
        seconds=current_app.config.get('JWT_ACCESS_TOKEN_EXPIRES', 24 * 3600)
    )
    payload = {
        'sub': user.id,
        'username': user.username,
        'is_admin': bool(user.is_admin),
        'jti': str(uuid.uuid4()),
        'iat': now,
        'exp': now + expires_delta,
    }
    token = jwt.encode(
        payload,
        current_app.config['JWT_SECRET_KEY'],
        algorithm='HS256'
    )
    # PyJWT >= 2 返回 str，< 2 返回 bytes
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    return token


def decode_token(token):
    """解码并验证 JWT

    返回 (payload, None) 或 (None, error_reason)
    """
    try:
        payload = jwt.decode(
            token,
            current_app.config['JWT_SECRET_KEY'],
            algorithms=['HS256']
        )
        return payload, None
    except jwt.ExpiredSignatureError:
        return None, 'token_expired'
    except jwt.InvalidTokenError:
        return None, 'invalid_token'


def _is_token_blacklisted(jti):
    """检查 token 是否在黑名单"""
    return jti in _token_blacklist


def _add_token_to_blacklist(jti, exp):
    """将 token 加入黑名单"""
    import time
    _token_blacklist[jti] = exp
    # 顺手清理已过期的黑名单项，避免内存泄漏
    # 注意：使用 time.time() 而非 datetime.utcnow().timestamp()，
    # 因为后者在非 UTC 时区会返回带时区偏移的值
    now_ts = time.time()
    for k in list(_token_blacklist.keys()):
        if _token_blacklist[k] < now_ts:
            del _token_blacklist[k]


def _load_user_from_token():
    """从请求头解析 token 并加载用户

    成功：g.current_user / g.token_jti / g.token_payload 被设置，返回 user
    失败：返回 None（不抛异常，供灰度阶段使用）
    """
    if getattr(g, 'current_user', None) is not None:
        return g.current_user

    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None
    token = auth_header[7:].strip()
    if not token:
        return None

    payload, err = decode_token(token)
    if err or not payload:
        return None
    if _is_token_blacklisted(payload.get('jti', '')):
        return None

    User = _get_user_model()
    session = _get_session()
    try:
        user = session.query(User).filter_by(
            id=payload['sub'], is_active=True
        ).first()
    except Exception:
        return None

    if not user:
        return None

    g.current_user = user
    g.token_jti = payload.get('jti')
    g.token_payload = payload
    return user


# ============================================================
# 装饰器
# ============================================================
def auth_required(f):
    """要求登录的装饰器

    P3 阶段会在业务 API 上批量添加此装饰器。
    P1 阶段仅 auth 相关 API 使用。
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        user = _load_user_from_token()
        if not user:
            return jsonify({
                'error': '未登录或登录已过期',
                'code': 'UNAUTHORIZED'
            }), 401
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    """要求管理员权限"""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = _load_user_from_token()
        if not user:
            return jsonify({
                'error': '未登录或登录已过期',
                'code': 'UNAUTHORIZED'
            }), 401
        if not user.is_admin:
            return jsonify({
                'error': '需要管理员权限',
                'code': 'FORBIDDEN'
            }), 403
        return f(*args, **kwargs)
    return decorated


def get_current_user():
    """获取当前登录用户（不报错）

    用于 P1 灰度阶段：业务 API 可调用此函数尝试获取用户，
    若无 token 则返回 None，不影响现有逻辑。
    """
    return _load_user_from_token()


# ============================================================
# 校验工具
# ============================================================
def _validate_username(username):
    if not username or not isinstance(username, str):
        return False, '用户名不能为空'
    if len(username) < 3 or len(username) > 50:
        return False, '用户名长度需为 3-50 个字符'
    if not username.replace('_', '').replace('-', '').isalnum():
        return False, '用户名仅支持字母、数字、下划线、连字符'
    return True, None


def _validate_password(password):
    if not password or not isinstance(password, str):
        return False, '密码不能为空'
    if len(password) < 8 or len(password) > 128:
        return False, '密码长度需为 8-128 个字符'
    return True, None


# ============================================================
# Auth API 路由
# ============================================================
@bp.route('/register', methods=['POST'])
def register():
    """注册新用户

    - 首个注册的用户自动成为管理员（is_admin=1）
    - 后续注册用户为普通用户
    - 注册成功后返回 JWT（免再次登录）
    """
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''
    display_name = (data.get('display_name') or '').strip() or None

    ok, msg = _validate_username(username)
    if not ok:
        return jsonify({'error': msg, 'code': 'VALIDATION_ERROR'}), 400
    ok, msg = _validate_password(password)
    if not ok:
        return jsonify({'error': msg, 'code': 'VALIDATION_ERROR'}), 400

    User = _get_user_model()
    session = _get_session()
    try:
        existing = session.query(User).filter_by(username=username).first()
        if existing:
            return jsonify({'error': '用户名已存在', 'code': 'USERNAME_EXISTS'}), 409

        # 首个用户自动成为管理员
        user_count = session.query(User).count()
        is_admin = (user_count == 0)

        user = User(
            username=username,
            display_name=display_name or username,
            is_admin=is_admin,
            is_active=True,
        )
        user.set_password(password)
        session.add(user)
        session.commit()
        session.refresh(user)

        token = generate_token(user)
        return jsonify({
            'message': '注册成功',
            'token': token,
            'user': user.to_dict(),
        }), 201
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'注册失败: {e}', 'code': 'INTERNAL_ERROR'}), 500
    finally:
        session.close()


@bp.route('/login', methods=['POST'])
def login():
    """登录，返回 JWT"""
    data = request.get_json(silent=True) or {}
    username = (data.get('username') or '').strip()
    password = data.get('password') or ''

    if not username or not password:
        return jsonify({'error': '用户名和密码不能为空', 'code': 'VALIDATION_ERROR'}), 400

    User = _get_user_model()
    session = _get_session()
    try:
        user = session.query(User).filter_by(username=username).first()
        if not user or not user.check_password(password):
            return jsonify({'error': '用户名或密码错误', 'code': 'INVALID_CREDENTIALS'}), 401
        if not user.is_active:
            return jsonify({'error': '账户已被禁用', 'code': 'ACCOUNT_DISABLED'}), 403

        token = generate_token(user)
        return jsonify({
            'message': '登录成功',
            'token': token,
            'user': user.to_dict(),
        }), 200
    except Exception as e:
        return jsonify({'error': f'登录失败: {e}', 'code': 'INTERNAL_ERROR'}), 500
    finally:
        session.close()


@bp.route('/me', methods=['GET'])
@auth_required
def me():
    """获取当前登录用户信息"""
    return jsonify({
        'user': g.current_user.to_dict()
    }), 200


@bp.route('/logout', methods=['POST'])
@auth_required
def logout():
    """登出，将当前 token 加入黑名单"""
    jti = getattr(g, 'token_jti', None)
    payload = getattr(g, 'token_payload', None) or {}
    exp = payload.get('exp')
    if jti and exp:
        _add_token_to_blacklist(jti, exp)
    return jsonify({'message': '已登出'}), 200


# ============================================================
# 用户管理 API（/api/users）
# ============================================================
@users_bp.route('', methods=['GET'])
@admin_required
def list_users():
    """用户列表（仅管理员）"""
    User = _get_user_model()
    session = _get_session()
    try:
        users = session.query(User).order_by(User.id).all()
        return jsonify({
            'users': [u.to_dict() for u in users]
        }), 200
    finally:
        session.close()


@users_bp.route('/<int:user_id>', methods=['PUT'])
@auth_required
def update_user(user_id):
    """更新用户信息

    - 本人可修改自己的 display_name / password
    - 管理员可额外修改 is_admin / is_active
    """
    current = g.current_user
    if current.id != user_id and not current.is_admin:
        return jsonify({'error': '无权修改他人信息', 'code': 'FORBIDDEN'}), 403

    data = request.get_json(silent=True) or {}
    User = _get_user_model()
    session = _get_session()
    try:
        user = session.query(User).filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': '用户不存在', 'code': 'NOT_FOUND'}), 404

        # 通用字段
        if 'display_name' in data:
            user.display_name = (data['display_name'] or '').strip() or None

        # 修改密码：需提供 old_password 校验（管理员重置他人密码除外）
        if 'password' in data:
            new_pwd = data['password'] or ''
            ok, msg = _validate_password(new_pwd)
            if not ok:
                return jsonify({'error': msg, 'code': 'VALIDATION_ERROR'}), 400
            # 非管理员修改密码必须校验旧密码
            if not current.is_admin or current.id == user.id:
                old_pwd = data.get('old_password') or ''
                if not user.check_password(old_pwd):
                    return jsonify({'error': '原密码错误', 'code': 'INVALID_OLD_PASSWORD'}), 400
            user.set_password(new_pwd)

        # 管理员专属字段
        if current.is_admin:
            if 'is_admin' in data:
                # 防止把自己降级导致无管理员
                if current.id == user.id and not data['is_admin']:
                    return jsonify({'error': '不能取消自己的管理员权限', 'code': 'FORBIDDEN'}), 400
                user.is_admin = bool(data['is_admin'])
            if 'is_active' in data:
                if current.id == user.id and not data['is_active']:
                    return jsonify({'error': '不能禁用自己的账户', 'code': 'FORBIDDEN'}), 400
                user.is_active = bool(data['is_active'])

        session.commit()
        session.refresh(user)
        return jsonify({
            'message': '更新成功',
            'user': user.to_dict()
        }), 200
    except Exception as e:
        session.rollback()
        return jsonify({'error': f'更新失败: {e}', 'code': 'INTERNAL_ERROR'}), 500
    finally:
        session.close()
