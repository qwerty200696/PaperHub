"""
时光清单 API - 待办、纪念日、番茄钟数据持久化
数据存储在 data/timelist.json
"""
import json
import threading
from pathlib import Path
from flask import Blueprint, jsonify, request

bp = Blueprint('timelist', __name__, url_prefix='/api/timelist')

DATA_FILE = Path(__file__).parent.parent.parent / 'data' / 'timelist.json'
DATA_FILE.parent.mkdir(parents=True, exist_ok=True)

_lock = threading.Lock()


def _load_data():
    if DATA_FILE.exists():
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return {
        'todos': [],
        'memorials': [],
        'pomodoroStats': [],
        'settings': {'focusMinutes': 25, 'breakMinutes': 5},
        'initialized': False,
        'notified': []
    }


def _save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"保存时光清单数据失败: {e}")
        return False


@bp.route('/data', methods=['GET'])
def get_all_data():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'data': data})


@bp.route('/data', methods=['PUT'])
def save_all_data():
    with _lock:
        incoming = request.get_json(silent=True) or {}
        current = _load_data()
        if 'todos' in incoming:
            current['todos'] = incoming['todos']
        if 'memorials' in incoming:
            current['memorials'] = incoming['memorials']
        if 'pomodoroStats' in incoming:
            current['pomodoroStats'] = incoming['pomodoroStats']
        if 'settings' in incoming:
            current['settings'] = incoming['settings']
        if 'initialized' in incoming:
            current['initialized'] = incoming['initialized']
        if 'notified' in incoming:
            current['notified'] = incoming['notified']
        ok = _save_data(current)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/todos', methods=['GET'])
def get_todos():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'todos': data.get('todos', [])})


@bp.route('/todos', methods=['PUT'])
def save_todos():
    with _lock:
        todos = (request.get_json(silent=True) or {}).get('todos', [])
        data = _load_data()
        data['todos'] = todos
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/todos', methods=['POST'])
def add_todo():
    with _lock:
        todo = request.get_json(silent=True) or {}
        data = _load_data()
        data['todos'].append(todo)
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True, 'todo': todo})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/memorials', methods=['GET'])
def get_memorials():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'memorials': data.get('memorials', [])})


@bp.route('/memorials', methods=['PUT'])
def save_memorials():
    with _lock:
        memorials = (request.get_json(silent=True) or {}).get('memorials', [])
        data = _load_data()
        data['memorials'] = memorials
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/settings', methods=['GET'])
def get_settings():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'settings': data.get('settings', {})})


@bp.route('/settings', methods=['PUT'])
def save_settings():
    with _lock:
        settings = (request.get_json(silent=True) or {}).get('settings', {})
        data = _load_data()
        data['settings'] = settings
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/pomodoro-stats', methods=['GET'])
def get_pomodoro_stats():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'pomodoroStats': data.get('pomodoroStats', [])})


@bp.route('/pomodoro-stats', methods=['PUT'])
def save_pomodoro_stats():
    with _lock:
        stats = (request.get_json(silent=True) or {}).get('pomodoroStats', [])
        data = _load_data()
        data['pomodoroStats'] = stats
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500


@bp.route('/notified', methods=['GET'])
def get_notified():
    with _lock:
        data = _load_data()
    return jsonify({'success': True, 'notified': data.get('notified', [])})


@bp.route('/notified', methods=['PUT'])
def save_notified():
    with _lock:
        notified = (request.get_json(silent=True) or {}).get('notified', [])
        data = _load_data()
        data['notified'] = notified
        ok = _save_data(data)
    if ok:
        return jsonify({'success': True})
    return jsonify({'success': False, 'error': '保存失败'}), 500
