"""
Backup API - 数据备份与恢复
支持导出/导入 SQLite + files 压缩包
"""
from flask import Blueprint, jsonify, request, send_file
from pathlib import Path
from datetime import datetime
import shutil
import zipfile
import os
import tempfile

bp = Blueprint('backup', __name__)


def get_config_paths():
    """获取配置路径"""
    try:
        from backend.config import BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR
    except ImportError:
        from config import BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR
    return BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR


def _create_backup_zip(backup_path, db_path, papers_dir):
    """创建备份压缩包"""
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        # 添加数据库文件
        if db_path.exists():
            zf.write(db_path, arcname='db/paperhub.db')

        # 添加 papers 目录下的所有文件
        if papers_dir.exists():
            for file_path in papers_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(papers_dir.parent)
                    zf.write(file_path, arcname=str(arcname))


def _extract_backup_zip(zip_path, extract_dir):
    """解压备份压缩包"""
    with zipfile.ZipFile(zip_path, 'r') as zf:
        zf.extractall(extract_dir)


@bp.route('/backup/export', methods=['POST'])
def export_backup():
    """
    导出数据备份

    请求体（可选）:
    {
        "filename": "custom_name"  // 自定义文件名（不含扩展名）
    }

    返回: ZIP 文件下载
    """
    try:
        BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR = get_config_paths()

        data = request.get_json(silent=True) or {}
        custom_name = data.get('filename', '').strip()

        # 生成文件名
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if custom_name:
            filename = f"{custom_name}_{timestamp}.zip"
        else:
            filename = f"paperhub_backup_{timestamp}.zip"

        backup_path = BACKUPS_DIR / filename

        # 确保备份目录存在
        BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

        db_path = DB_DIR / 'paperhub.db'

        # 创建压缩包
        _create_backup_zip(backup_path, db_path, PAPERS_DIR)

        # 返回文件
        return send_file(
            str(backup_path),
            as_attachment=True,
            download_name=filename,
            mimetype='application/zip'
        )

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/backup/import', methods=['POST'])
def import_backup():
    """
    导入数据备份（会覆盖现有数据，请谨慎使用）

    请求: multipart/form-data，包含 backup_file 字段

    返回:
    {
        "message": "恢复成功",
        "restored_files": 123,
        "db_restored": true
    }
    """
    try:
        BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR = get_config_paths()

        if 'backup_file' not in request.files:
            return jsonify({'error': '请上传备份文件'}), 400

        file = request.files['backup_file']
        if file.filename == '':
            return jsonify({'error': '未选择文件'}), 400

        if not file.filename.endswith('.zip'):
            return jsonify({'error': '只支持 .zip 格式的备份文件'}), 400

        # 创建临时目录
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            zip_path = temp_path / 'backup.zip'
            file.save(zip_path)

            # 解压
            extract_dir = temp_path / 'extracted'
            extract_dir.mkdir()
            _extract_backup_zip(zip_path, extract_dir)

            restored_files = 0
            db_restored = False

            # 恢复数据库
            db_backup = extract_dir / 'db' / 'paperhub.db'
            if db_backup.exists():
                DB_DIR.mkdir(parents=True, exist_ok=True)
                db_target = DB_DIR / 'paperhub.db'

                # 如果数据库正在使用，先备份当前数据库
                if db_target.exists():
                    auto_backup = BACKUPS_DIR / f"auto_backup_before_import_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
                    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(db_target, auto_backup)

                shutil.copy2(db_backup, db_target)
                db_restored = True
                restored_files += 1

            # 恢复 papers 文件
            papers_backup = extract_dir / 'papers'
            if papers_backup.exists():
                PAPERS_DIR.mkdir(parents=True, exist_ok=True)

                for src_file in papers_backup.rglob('*'):
                    if src_file.is_file():
                        rel_path = src_file.relative_to(papers_backup)
                        dst_file = PAPERS_DIR / rel_path
                        dst_file.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(src_file, dst_file)
                        restored_files += 1

            return jsonify({
                'message': '数据恢复成功',
                'restored_files': restored_files,
                'db_restored': db_restored
            })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/backup/list', methods=['GET'])
def list_backups():
    """
    获取备份文件列表

    返回:
    {
        "backups": [
            {
                "filename": "paperhub_backup_20260511_120000.zip",
                "size": "12.5MB",
                "created_at": "2026-05-11 12:00:00"
            }
        ]
    }
    """
    try:
        _, _, _, _, BACKUPS_DIR = get_config_paths()

        backups = []
        if BACKUPS_DIR.exists():
            for backup_file in sorted(BACKUPS_DIR.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True):
                size_bytes = backup_file.stat().st_size
                if size_bytes < 1024:
                    size_str = f"{size_bytes}B"
                elif size_bytes < 1024 * 1024:
                    size_str = f"{size_bytes / 1024:.1f}KB"
                else:
                    size_str = f"{size_bytes / (1024 * 1024):.1f}MB"

                created_at = datetime.fromtimestamp(backup_file.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')

                backups.append({
                    'filename': backup_file.name,
                    'size': size_str,
                    'created_at': created_at
                })

        return jsonify({'backups': backups})

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@bp.route('/backup/delete', methods=['POST'])
def delete_backup():
    """
    删除备份文件

    请求体:
    {
        "filename": "paperhub_backup_20260511_120000.zip"
    }
    """
    try:
        _, _, _, _, BACKUPS_DIR = get_config_paths()

        data = request.get_json() or {}
        filename = data.get('filename', '').strip()

        if not filename:
            return jsonify({'error': 'filename is required'}), 400

        # 防止路径遍历
        if '..' in filename or '/' in filename or '\\' in filename:
            return jsonify({'error': '非法文件名'}), 400

        backup_file = BACKUPS_DIR / filename
        if not backup_file.exists():
            return jsonify({'error': '备份文件不存在'}), 404

        backup_file.unlink()
        return jsonify({'message': '备份文件已删除'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500
