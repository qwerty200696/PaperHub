"""
飞书消息 API - 使用 lark-cli 获取飞书群聊和消息
"""
import os
import json
import subprocess
import tempfile
from pathlib import Path
from flask import Blueprint, jsonify, request
from datetime import datetime

bp = Blueprint('feishu', __name__, url_prefix='/api/feishu')

# 离线消息存储目录
OFFLINE_MESSAGES_DIR = Path(__file__).parent.parent.parent / 'data' / 'feishu_messages'
OFFLINE_MESSAGES_DIR.mkdir(parents=True, exist_ok=True)

# 置顶群聊存储文件（存储完整群聊信息，避免每次调用API）
PINNED_CHATS_FILE = Path(__file__).parent.parent.parent / 'data' / 'feishu_pinned_chats.json'


def _load_pinned_chats():
    """加载置顶群聊列表（返回对象数组，包含缓存的群信息）"""
    if PINNED_CHATS_FILE.exists():
        try:
            with open(PINNED_CHATS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 兼容旧格式（纯字符串数组）和新格式（对象数组）
                if data and isinstance(data[0], str):
                    return [{'chat_id': cid, 'name': None} for cid in data]
                return data
        except:
            pass
    return []


def _save_pinned_chats(pinned_chats):
    """保存置顶群聊列表（对象数组，含缓存信息）"""
    try:
        with open(PINNED_CHATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(pinned_chats, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"保存置顶群聊失败: {e}")


def _get_chat_info(chat_id, as_identity='user', app_id=None, app_secret=None):
    """获取单个群聊信息（优先使用 chat-list，兼容外部群）"""
    try:
        # 方案1: 使用 +chat-list 获取所有群聊，然后匹配（支持外部群）
        # 最多翻2页，获取200个群聊
        all_chats = []
        page_token = None
        for _ in range(2):
            cmd = ['im', '+chat-list', '--page-size', '100']
            if page_token:
                cmd.extend(['--page-token', page_token])
            result = run_lark_cli(
                cmd,
                as_identity=as_identity,
                app_id=app_id,
                app_secret=app_secret
            )
            if result['success']:
                chat_data = result['data'].get('data', {})
                all_chats.extend(chat_data.get('chats', []))
                page_token = chat_data.get('page_token')
                if not chat_data.get('has_more'):
                    break
            else:
                break

        for chat in all_chats:
            if chat.get('chat_id') == chat_id:
                return {
                    'chat_id': chat.get('chat_id'),
                    'name': chat.get('name', '未命名群聊'),
                    'description': chat.get('description', ''),
                    'owner_id': chat.get('owner_id'),
                    'avatar_key': chat.get('avatar_key'),
                    'external': chat.get('external', False),
                    'chat_status': chat.get('chat_status', 'normal'),
                    'member_count': chat.get('member_count', 0)
                }

        # 方案2: 如果 chat-list 没找到，尝试 chats get（内部群）
        result = run_lark_cli(
            ['im', 'chats', 'get', '--params', json.dumps({'chat_id': chat_id})],
            as_identity=as_identity,
            app_id=app_id,
            app_secret=app_secret
        )
        if result['success']:
            chat = result['data'].get('data', {})
            return {
                'chat_id': chat.get('chat_id'),
                'name': chat.get('name', '未命名群聊'),
                'description': chat.get('description', ''),
                'owner_id': chat.get('owner_id'),
                'avatar_key': chat.get('avatar_key'),
                'external': chat.get('external', False),
                'chat_status': chat.get('chat_status', 'normal'),
                'member_count': chat.get('member_count', 0)
            }
    except Exception as e:
        print(f"获取群聊信息失败 {chat_id}: {e}")
    return None


def run_lark_cli(command_args, as_identity='bot', app_id=None, app_secret=None):
    """
    执行 lark-cli 命令
    
    Args:
        command_args: 命令参数列表
        as_identity: 身份类型 'bot' 或 'user'
        app_id: 飞书应用ID（bot身份时需要）
        app_secret: 飞书应用密钥（bot身份时需要）
    
    Returns:
        dict: 解析后的JSON响应
    """
    try:
        # 构建完整命令（使用绝对路径）
        lark_cli_path = os.environ.get('LARK_CLI_PATH', 'lark-cli')
        cmd = [lark_cli_path] + command_args
        
        # 添加身份标识
        if as_identity == 'bot':
            cmd.extend(['--as', 'bot'])
        else:
            cmd.extend(['--as', 'user'])
        
        # 添加JSON输出格式
        cmd.extend(['--format', 'json'])
        
        # 执行命令
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=30,
            env={**os.environ}
        )
        
        # 检查退出码
        if result.returncode != 0:
            error_msg = result.stderr.strip()
            try:
                error_data = json.loads(error_msg)
                return {
                    'success': False,
                    'error': error_data.get('error', {}).get('message', error_msg),
                    'error_type': error_data.get('error', {}).get('type', 'unknown')
                }
            except json.JSONDecodeError:
                return {
                    'success': False,
                    'error': error_msg
                }
        
        # 解析JSON输出
        output = result.stdout.strip()
        if not output:
            return {
                'success': False,
                'error': '命令执行成功但无输出'
            }
        
        data = json.loads(output)
        return {
            'success': True,
            'data': data
        }
        
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'error': '命令执行超时'
        }
    except FileNotFoundError:
        return {
            'success': False,
            'error': 'lark-cli 未安装，请先安装: npm install -g @larksuite/lark-cli'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'执行失败: {str(e)}'
        }


def _format_chat_groups(chats):
    """格式化群聊数据为统一结构"""
    groups = []
    for chat in chats:
        name = chat.get('name')
        if not name or not name.strip():
            name = '未命名群聊'
        groups.append({
            'chat_id': chat.get('chat_id'),
            'name': name,
            'description': chat.get('description', ''),
            'owner_id': chat.get('owner_id'),
            'avatar_key': chat.get('avatar_key'),
            'external': chat.get('external', False),
            'chat_status': chat.get('chat_status', 'normal'),
            'member_count': chat.get('member_count', 0)
        })
    return groups


@bp.route('/groups', methods=['POST'])
def get_groups():
    """
    获取群聊列表
    POST /api/feishu/groups
    Body: { "appId": "...", "appSecret": "..." } (可选，用于bot身份)
    Query: ?sort_type=ByActiveTimeDesc&page_size=50&page_token=xxx&exclude_muted=true
    """
    try:
        data = request.get_json(silent=True) or {}
        app_id = data.get('appId')
        app_secret = data.get('appSecret')

        # 获取查询参数
        sort_type = request.args.get('sort_type', 'ByActiveTimeDesc')
        page_size = request.args.get('page_size', 50, type=int)
        page_token = request.args.get('page_token')
        exclude_muted = request.args.get('exclude_muted', 'false').lower() == 'true'

        # 确定身份类型
        as_identity = 'bot' if (app_id and app_secret) else 'user'

        # 构建命令参数
        cmd_args = ['im', '+chat-list']

        # 添加排序类型
        if sort_type in ['ByCreateTimeAsc', 'ByActiveTimeDesc']:
            cmd_args.extend(['--sort-type', sort_type])

        # 添加分页大小
        if 1 <= page_size <= 100:
            cmd_args.extend(['--page-size', str(page_size)])

        # 添加分页token
        if page_token:
            cmd_args.extend(['--page-token', page_token])

        # 添加排除免打扰群聊（仅user身份有效）
        if exclude_muted and as_identity == 'user':
            cmd_args.append('--exclude-muted')

        # 执行命令
        result = run_lark_cli(cmd_args, as_identity=as_identity, app_id=app_id, app_secret=app_secret)

        if not result['success']:
            return jsonify(result), 400

        # 提取群聊数据
        chat_data = result['data'].get('data', {})
        chats = chat_data.get('chats', [])
        has_more = chat_data.get('has_more', False)
        page_token_next = chat_data.get('page_token', '')

        groups = _format_chat_groups(chats)

        return jsonify({
            'success': True,
            'groups': groups,
            'has_more': has_more,
            'page_token': page_token_next,
            'total': len(groups)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取群聊列表失败: {str(e)}'
        }), 500


@bp.route('/test', methods=['GET'])
def test_cli():
    """
    测试飞书 CLI 连接状态
    GET /api/feishu/test
    """
    try:
        result = run_lark_cli(['im', '+chat-list', '--page-size', '1'], as_identity='user')
        if result['success']:
            return jsonify({
                'success': True,
                'message': '飞书 CLI 连接正常，用户身份已登录'
            }), 200
        else:
            error_msg = result.get('error', '未知错误')
            if '未安装' in error_msg or 'FileNotFoundError' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'lark-cli 未安装，请先执行: npm install -g @larksuite/lark-cli'
                }), 200
            elif '登录' in error_msg or 'auth' in error_msg.lower() or 'token' in error_msg.lower() or '身份' in error_msg:
                return jsonify({
                    'success': False,
                    'error': 'lark-cli 未登录，请先执行: lark-cli auth login'
                }), 200
            else:
                return jsonify({
                    'success': False,
                    'error': f'连接失败: {error_msg}'
                }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'测试连接异常: {str(e)}'
        }), 500


@bp.route('/pinned', methods=['GET', 'POST', 'DELETE'])
def pinned_chats():
    """
    置顶群聊管理
    GET    /api/feishu/pinned     -> 获取置顶群聊列表（直接读本地缓存，不调用API）
    POST   /api/feishu/pinned     -> { "chatId": "oc_xxx", "name": "群名称" } 添加置顶
    DELETE /api/feishu/pinned     -> { "chatId": "oc_xxx" } 取消置顶
    """
    try:
        data = request.get_json(silent=True) or {}

        if request.method == 'GET':
            # 直接返回本地缓存，不调用飞书API
            pinned = _load_pinned_chats()
            # 过滤掉 name 为 None 的（兼容旧数据），并构建返回格式
            pinned_groups = []
            pinned_ids = []
            for item in pinned:
                cid = item.get('chat_id') if isinstance(item, dict) else item
                name = item.get('name') if isinstance(item, dict) else None
                pinned_ids.append(cid)
                pinned_groups.append({
                    'chat_id': cid,
                    'name': name or '未命名群聊',
                    'member_count': item.get('member_count', 0) if isinstance(item, dict) else 0,
                    'external': item.get('external', False) if isinstance(item, dict) else False
                })

            return jsonify({
                'success': True,
                'pinnedChatIds': pinned_ids,
                'pinnedGroups': pinned_groups
            }), 200

        chat_id = data.get('chatId')

        if not chat_id:
            return jsonify({
                'success': False,
                'error': 'chatId 不能为空'
            }), 400

        pinned = _load_pinned_chats()

        if request.method == 'POST':
            # 检查是否已存在
            existing_ids = [p.get('chat_id') if isinstance(p, dict) else p for p in pinned]
            if chat_id not in existing_ids:
                # 置顶时缓存群名称等信息
                new_item = {
                    'chat_id': chat_id,
                    'name': data.get('name', '未命名群聊'),
                    'member_count': data.get('member_count', 0),
                    'external': data.get('external', False),
                    'pinned_at': datetime.now().isoformat()
                }
                pinned.insert(0, new_item)
                _save_pinned_chats(pinned)
            return jsonify({
                'success': True,
                'message': '已置顶',
                'pinnedChatIds': [p.get('chat_id') if isinstance(p, dict) else p for p in pinned]
            }), 200

        if request.method == 'DELETE':
            pinned = [p for p in pinned if (p.get('chat_id') if isinstance(p, dict) else p) != chat_id]
            _save_pinned_chats(pinned)
            return jsonify({
                'success': True,
                'message': '已取消置顶',
                'pinnedChatIds': [p.get('chat_id') if isinstance(p, dict) else p for p in pinned]
            }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'操作失败: {str(e)}'
        }), 500


@bp.route('/groups/search', methods=['POST'])
def search_groups():
    """
    搜索群聊（服务端关键词搜索）
    POST /api/feishu/groups/search
    Body: {
        "appId": "...",
        "appSecret": "...",
        "query": "关键词",
        "searchTypes": "private,public_joined",
        "page_size": 20,
        "page_token": ""
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        app_id = data.get('appId')
        app_secret = data.get('appSecret')
        query = data.get('query', '')

        if not query:
            return jsonify({
                'success': False,
                'error': 'query 参数不能为空'
            }), 400

        # 确定身份类型
        as_identity = 'bot' if (app_id and app_secret) else 'user'

        # 构建命令参数
        cmd_args = ['im', '+chat-search', '--query', query]

        # 可选：搜索类型过滤
        search_types = data.get('searchTypes')
        if search_types:
            cmd_args.extend(['--search-types', search_types])

        # 分页大小
        page_size = data.get('page_size', 20)
        if isinstance(page_size, int) and 1 <= page_size <= 100:
            cmd_args.extend(['--page-size', str(page_size)])

        # 分页token
        page_token = data.get('page_token')
        if page_token:
            cmd_args.extend(['--page-token', page_token])

        # 执行命令
        result = run_lark_cli(cmd_args, as_identity=as_identity, app_id=app_id, app_secret=app_secret)

        if not result['success']:
            return jsonify(result), 400

        # 提取群聊数据
        chat_data = result['data'].get('data', {})
        chats = chat_data.get('chats', [])
        has_more = chat_data.get('has_more', False)
        page_token_next = chat_data.get('page_token', '')

        groups = _format_chat_groups(chats)

        return jsonify({
            'success': True,
            'groups': groups,
            'has_more': has_more,
            'page_token': page_token_next,
            'total': len(groups)
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'搜索群聊失败: {str(e)}'
        }), 500


@bp.route('/messages', methods=['POST'])
def get_messages():
    """
    获取群聊消息
    POST /api/feishu/messages
    Body: { 
        "chatId": "oc_xxx", 
        "appId": "...", 
        "appSecret": "...",
        "start": "2026-03-10T00:00:00+08:00",
        "end": "2026-03-11T00:00:00+08:00",
        "sort": "desc",
        "page_size": 50,
        "page_token": "xxx"
    }
    """
    try:
        data = request.get_json(silent=True) or {}
        chat_id = data.get('chatId')
        app_id = data.get('appId')
        app_secret = data.get('appSecret')
        
        if not chat_id:
            return jsonify({
                'success': False,
                'error': 'chatId 参数不能为空'
            }), 400
        
        # 获取其他参数
        start_time = data.get('start')
        end_time = data.get('end')
        sort = data.get('sort', 'asc')  # 默认升序，因为某些群聊降序可能返回空
        page_size = data.get('page_size', 50)
        if not isinstance(page_size, int):
            try:
                page_size = int(page_size)
            except (ValueError, TypeError):
                page_size = 50
        page_token = data.get('page_token')
        
        # 确定身份类型
        as_identity = 'bot' if (app_id and app_secret) else 'user'
        
        # 构建命令参数
        cmd_args = ['im', '+chat-messages-list', '--chat-id', chat_id]
        
        # 添加时间范围
        if start_time:
            cmd_args.extend(['--start', start_time])
        if end_time:
            cmd_args.extend(['--end', end_time])
        
        # 添加排序
        if sort in ['asc', 'desc']:
            cmd_args.extend(['--sort', sort])
        
        # 添加分页大小（最大50）
        if 1 <= page_size <= 50:
            cmd_args.extend(['--page-size', str(page_size)])
        
        # 添加分页token
        if page_token:
            cmd_args.extend(['--page-token', page_token])
        
        # 执行命令
        result = run_lark_cli(cmd_args, as_identity=as_identity, app_id=app_id, app_secret=app_secret)
        
        if not result['success']:
            return jsonify(result), 400
        
        # 提取消息数据
        msg_data = result['data'].get('data', {})
        # lark-cli返回的字段是'messages'而不是'items'
        messages = msg_data.get('messages', [])
        has_more = msg_data.get('has_more', False)
        page_token_next = msg_data.get('page_token', '')
        
        # 注意：飞书 API 返回的 sender 中，机器人(sender_type=app)没有 name 字段
        # 外部群成员也可能没有 name 字段（权限限制）
        # 这里不再尝试通过 contact API 获取，因为外部群成员也无法获取

        # 格式化消息
        formatted_messages = []
        for msg in messages:
            # 跳过已撤回的消息
            if msg.get('deleted'):
                continue

            sender = msg.get('sender', {}) or {}

            # 获取content - lark-cli返回的content在顶层，不在body里
            content = msg.get('content', '')

            # 如果content是JSON字符串（富文本消息），尝试解析
            try:
                if isinstance(content, str) and content.startswith('{'):
                    content_obj = json.loads(content)
                    # 提取文本内容
                    if 'text' in content_obj:
                        content = content_obj['text']
                    elif 'post' in content_obj:
                        # 处理富文本
                        content = _extract_post_text(content_obj['post'])
            except:
                pass

            # 解析 sender_name
            sender_name = _resolve_sender_name(sender)

            formatted_messages.append({
                'message_id': msg.get('message_id'),
                'msg_type': msg.get('msg_type', 'text'),
                'sender_name': sender_name,
                'sender_id': sender.get('id') or sender.get('sender_id'),
                'sender_type': sender.get('sender_type', 'user'),
                'create_time': msg.get('create_time'),
                'update_time': msg.get('update_time'),
                'content': content,
                'mentions': msg.get('mentions') if isinstance(msg.get('mentions'), list) else [],
                'thread_id': msg.get('thread_id'),
                'updated': msg.get('updated', False)
            })
        
        return jsonify({
            'success': True,
            'messages': formatted_messages,
            'has_more': has_more,
            'page_token': page_token_next,
            'total': len(formatted_messages)
        }), 200
        
    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        print(f"❌ 获取消息异常: {e}")
        print(f"Traceback:\n{error_trace}")
        return jsonify({
            'success': False,
            'error': f'获取消息失败: {str(e)}'
        }), 500


@bp.route('/offline/save', methods=['POST'])
def save_offline_messages():
    """
    保存消息到离线缓存
    POST /api/feishu/offline/save
    Body: {
        "chatId": "oc_xxx",
        "chatName": "群聊名称",
        "messages": [...],
        "savedAt": "2026-05-28T10:00:00"
    }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        chat_id = data.get('chatId')
        chat_name = data.get('chatName', '未命名群聊')
        messages = data.get('messages', [])
        
        if not chat_id:
            return jsonify({'error': 'chatId 不能为空'}), 400
        
        # 生成文件名（使用chatId避免特殊字符问题）
        filename = f"{chat_id}.json"
        filepath = OFFLINE_MESSAGES_DIR / filename
        
        # 读取现有数据（如果存在）
        existing_data = {}
        if filepath.exists():
            with open(filepath, 'r', encoding='utf-8') as f:
                existing_data = json.load(f)
        
        # 合并消息（去重）
        existing_messages = existing_data.get('messages', [])
        existing_ids = {msg.get('message_id') for msg in existing_messages if msg.get('message_id')}
        
        new_messages = [msg for msg in messages if msg.get('message_id') not in existing_ids]
        all_messages = existing_messages + new_messages
        
        # 按创建时间排序（最新的在前）
        all_messages.sort(key=lambda x: x.get('create_time', ''), reverse=True)
        
        # 保存数据
        save_data = {
            'chatId': chat_id,
            'chatName': chat_name,
            'messages': all_messages,
            'savedAt': data.get('savedAt') or datetime.now().isoformat(),
            'totalMessages': len(all_messages),
            'lastUpdated': datetime.now().isoformat()
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        return jsonify({
            'success': True,
            'message': f'已保存 {len(new_messages)} 条新消息，共 {len(all_messages)} 条',
            'totalMessages': len(all_messages)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'保存失败: {str(e)}'
        }), 500


@bp.route('/offline/list', methods=['GET'])
def list_offline_messages():
    """
    获取离线消息列表
    GET /api/feishu/offline/list
    """
    try:
        offline_files = list(OFFLINE_MESSAGES_DIR.glob('*.json'))
        
        offline_list = []
        for filepath in offline_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                offline_list.append({
                    'chatId': data.get('chatId'),
                    'chatName': data.get('chatName', '未命名群聊'),
                    'totalMessages': data.get('totalMessages', 0),
                    'savedAt': data.get('savedAt'),
                    'lastUpdated': data.get('lastUpdated')
                })
            except:
                continue
        
        # 按最后更新时间排序
        offline_list.sort(key=lambda x: x.get('lastUpdated', ''), reverse=True)
        
        return jsonify({
            'success': True,
            'offlineList': offline_list,
            'total': len(offline_list)
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'获取离线列表失败: {str(e)}'
        }), 500


@bp.route('/offline/load', methods=['POST'])
def load_offline_messages():
    """
    加载指定群聊的离线消息
    POST /api/feishu/offline/load
    Body: { "chatId": "oc_xxx" }
    Query: ?offset=0&limit=50
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        chat_id = data.get('chatId')
        if not chat_id:
            return jsonify({'error': 'chatId 不能为空'}), 400
        
        # 获取分页参数
        offset = request.args.get('offset', 0, type=int)
        limit = request.args.get('limit', 50, type=int)
        
        # 读取文件
        filename = f"{chat_id}.json"
        filepath = OFFLINE_MESSAGES_DIR / filename
        
        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': '未找到该群聊的离线消息'
            }), 404
        
        with open(filepath, 'r', encoding='utf-8') as f:
            offline_data = json.load(f)
        
        messages = offline_data.get('messages', [])
        total = len(messages)
        
        # 分页
        paginated_messages = messages[offset:offset + limit]
        
        return jsonify({
            'success': True,
            'chatId': chat_id,
            'chatName': offline_data.get('chatName', '未命名群聊'),
            'messages': paginated_messages,
            'total': total,
            'offset': offset,
            'limit': limit,
            'hasMore': offset + limit < total,
            'savedAt': offline_data.get('savedAt')
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'加载失败: {str(e)}'
        }), 500


@bp.route('/offline/delete', methods=['POST'])
def delete_offline_messages():
    """
    删除指定群聊的离线消息
    POST /api/feishu/offline/delete
    Body: { "chatId": "oc_xxx" }
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': '请求体不能为空'}), 400
        
        chat_id = data.get('chatId')
        if not chat_id:
            return jsonify({'error': 'chatId 不能为空'}), 400
        
        filename = f"{chat_id}.json"
        filepath = OFFLINE_MESSAGES_DIR / filename
        
        if not filepath.exists():
            return jsonify({
                'success': False,
                'error': '未找到该群聊的离线消息'
            }), 404
        
        filepath.unlink()
        
        return jsonify({
            'success': True,
            'message': '已删除离线消息'
        }), 200
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'删除失败: {str(e)}'
        }), 500


# 机器人名称映射表（app_id -> 名称）
# 注：飞书 API 不返回机器人名称，需手动维护映射
BOT_NAME_MAP = {
    'cli_a136ebe23478900b': '多维表格助手',
    'cli_c08abc1da138d00f': 'AIHOT小助手',
}


def _resolve_sender_name(sender):
    """
    解析消息发送者名称

    飞书 API 的 sender 结构：
    - 普通用户: {"id": "ou_xxx", "id_type": "open_id", "sender_type": "user", "name": "用户名"}
    - 机器人: {"id": "cli_xxx", "id_type": "app_id", "sender_type": "app"} (没有 name 字段)
    - 外部群成员: name 可能为 None（权限限制）

    Args:
        sender: 消息发送者对象

    Returns:
        str: 发送者显示名称
    """
    if not isinstance(sender, dict):
        return '未知用户'

    # 1. 优先使用 sender 中的 name 字段
    name = sender.get('name')
    if name:
        return name

    sender_type = sender.get('sender_type', 'user')
    sender_id = sender.get('id') or sender.get('sender_id')

    # 2. 如果是机器人 (app)，先查映射表
    if sender_type == 'app':
        if sender_id:
            # 查映射表
            mapped_name = BOT_NAME_MAP.get(sender_id)
            if mapped_name:
                return mapped_name
            return f'机器人 ({sender_id[-8:]})'
        return '机器人'

    # 3. 如果是用户但 name 为空（外部群成员权限限制）
    if sender_id:
        return f'用户 ({sender_id[-8:]})'

    return '未知用户'


def _extract_post_text(post_obj):
    """从富文本对象中提取纯文本"""
    texts = []
    
    def extract_from_content(content_list):
        for item in content_list:
            tag = item.get('tag')
            if tag == 'text':
                texts.append(item.get('text', ''))
            elif tag in ['a', 'mention', 'mention_user']:
                texts.append(item.get('text', item.get('user_id', '')))
            elif tag == 'img':
                texts.append('[图片]')
            elif 'children' in item:
                extract_from_content(item['children'])
    
    # post_obj 结构: {"zh_cn": {"title": "...", "content": [[...]]}}
    for lang, lang_data in post_obj.items():
        if isinstance(lang_data, dict) and 'content' in lang_data:
            for paragraph in lang_data['content']:
                if isinstance(paragraph, list):
                    extract_from_content(paragraph)
    
    return '\n'.join(texts) if texts else '[富文本消息]'
