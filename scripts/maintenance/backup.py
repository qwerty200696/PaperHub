#!/usr/bin/env python3
"""
Backup Script - 数据备份命令行工具

用法:
    python scripts/maintenance/backup.py              # 创建备份，自动命名
    python scripts/maintenance/backup.py -n mybackup  # 创建备份，自定义名称
    python scripts/maintenance/backup.py -l           # 列出所有备份

备份内容:
    - data/db/paperhub.db       SQLite 数据库
    - data/papers/              所有论文/文章/笔记文件

备份位置:
    data/backups/
"""
import argparse
import sys
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from backend.api.backup import _create_backup_zip, get_config_paths
except ImportError:
    # 直接导入逻辑，避免依赖 Flask 上下文
    from config import BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR
    import zipfile

    def _create_backup_zip(backup_path, db_path, papers_dir):
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            if db_path.exists():
                zf.write(db_path, arcname='db/paperhub.db')
            if papers_dir.exists():
                for file_path in papers_dir.rglob('*'):
                    if file_path.is_file():
                        arcname = file_path.relative_to(papers_dir.parent)
                        zf.write(file_path, arcname=str(arcname))

    def get_config_paths():
        return BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR


def create_backup(custom_name=None):
    """创建备份"""
    BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR = get_config_paths()

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if custom_name:
        filename = f"{custom_name}_{timestamp}.zip"
    else:
        filename = f"paperhub_backup_{timestamp}.zip"

    backup_path = BACKUPS_DIR / filename
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

    db_path = DB_DIR / 'paperhub.db'

    print(f"📦 正在创建备份: {filename}")
    print(f"   数据库: {db_path}")
    print(f"   文件目录: {PAPERS_DIR}")

    _create_backup_zip(backup_path, db_path, PAPERS_DIR)

    size_bytes = backup_path.stat().st_size
    if size_bytes < 1024 * 1024:
        size_str = f"{size_bytes / 1024:.1f} KB"
    else:
        size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

    print(f"✅ 备份完成: {backup_path}")
    print(f"   大小: {size_str}")
    return backup_path


def list_backups():
    """列出所有备份"""
    _, _, _, _, BACKUPS_DIR = get_config_paths()

    if not BACKUPS_DIR.exists():
        print("📂 备份目录不存在")
        return

    backups = sorted(BACKUPS_DIR.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not backups:
        print("📂 暂无备份文件")
        return

    print(f"📂 备份列表 ({len(backups)} 个):")
    print("-" * 60)
    for i, backup in enumerate(backups, 1):
        size_bytes = backup.stat().st_size
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        created = datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {i}. {backup.name:<45} {size_str:>10}  {created}")


def main():
    parser = argparse.ArgumentParser(description='PaperHub 数据备份工具')
    parser.add_argument('-n', '--name', help='自定义备份名称')
    parser.add_argument('-l', '--list', action='store_true', help='列出所有备份')

    args = parser.parse_args()

    if args.list:
        list_backups()
    else:
        create_backup(args.name)


if __name__ == '__main__':
    main()
