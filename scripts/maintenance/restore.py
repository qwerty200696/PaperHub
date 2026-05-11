#!/usr/bin/env python3
"""
Restore Script - 数据恢复命令行工具

用法:
    python scripts/maintenance/restore.py                    # 交互式选择备份恢复
    python scripts/maintenance/restore.py -f backup.zip      # 指定备份文件恢复
    python scripts/maintenance/restore.py -l                 # 列出可用备份

⚠️  警告: 恢复操作会覆盖现有数据！
    恢复前会自动创建当前数据的临时备份。
"""
import argparse
import shutil
import sys
import zipfile
from datetime import datetime
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

try:
    from backend.config import BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR
except ImportError:
    from config import BASE_DIR, DATA_DIR, DB_DIR, PAPERS_DIR, BACKUPS_DIR


def list_backups():
    """列出所有备份"""
    if not BACKUPS_DIR.exists():
        print("📂 备份目录不存在")
        return []

    backups = sorted(BACKUPS_DIR.glob('*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)

    if not backups:
        print("📂 暂无备份文件")
        return []

    print(f"📂 可用备份 ({len(backups)} 个):")
    print("-" * 60)
    for i, backup in enumerate(backups, 1):
        size_bytes = backup.stat().st_size
        if size_bytes < 1024 * 1024:
            size_str = f"{size_bytes / 1024:.1f} KB"
        else:
            size_str = f"{size_bytes / (1024 * 1024):.1f} MB"

        created = datetime.fromtimestamp(backup.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')
        print(f"  {i}. {backup.name:<45} {size_str:>10}  {created}")

    return backups


def restore_backup(backup_path):
    """执行恢复"""
    if not backup_path.exists():
        print(f"❌ 备份文件不存在: {backup_path}")
        return False

    print(f"⚠️  即将从 {backup_path.name} 恢复数据")
    print("   这会覆盖当前的 SQLite 数据库和 papers 目录下的所有文件！")
    confirm = input("   确认继续? [yes/no]: ").strip().lower()

    if confirm != 'yes':
        print("❌ 已取消")
        return False

    # 自动备份当前数据
    auto_backup_dir = BACKUPS_DIR
    auto_backup_dir.mkdir(parents=True, exist_ok=True)
    auto_backup_db = auto_backup_dir / f"auto_backup_before_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"

    db_target = DB_DIR / 'paperhub.db'
    if db_target.exists():
        print(f"📦 正在自动备份当前数据库...")
        shutil.copy2(db_target, auto_backup_db)
        print(f"   已保存到: {auto_backup_db}")

    # 解压备份
    import tempfile
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        extract_dir = temp_path / 'extracted'
        extract_dir.mkdir()

        print(f"📦 正在解压备份...")
        with zipfile.ZipFile(backup_path, 'r') as zf:
            zf.extractall(extract_dir)

        restored_files = 0

        # 恢复数据库
        db_backup = extract_dir / 'db' / 'paperhub.db'
        if db_backup.exists():
            DB_DIR.mkdir(parents=True, exist_ok=True)
            shutil.copy2(db_backup, db_target)
            print(f"✅ 数据库已恢复")
            restored_files += 1
        else:
            print(f"⚠️  备份中未找到数据库文件")

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

            print(f"✅ 已恢复 {restored_files - 1} 个文件到 papers 目录")
        else:
            print(f"⚠️  备份中未找到 papers 文件")

    print(f"\n🎉 恢复完成！共恢复 {restored_files} 个项目")
    return True


def interactive_restore():
    """交互式恢复"""
    backups = list_backups()
    if not backups:
        return

    try:
        choice = input("\n请输入要恢复的备份编号: ").strip()
        idx = int(choice) - 1
        if idx < 0 or idx >= len(backups):
            print("❌ 无效的编号")
            return
        backup_path = backups[idx]
    except ValueError:
        print("❌ 请输入数字")
        return

    restore_backup(backup_path)


def main():
    parser = argparse.ArgumentParser(description='PaperHub 数据恢复工具')
    parser.add_argument('-f', '--file', help='指定备份文件路径')
    parser.add_argument('-l', '--list', action='store_true', help='列出可用备份')

    args = parser.parse_args()

    if args.list:
        list_backups()
    elif args.file:
        backup_path = Path(args.file)
        if not backup_path.is_absolute():
            backup_path = BACKUPS_DIR / backup_path
        restore_backup(backup_path)
    else:
        interactive_restore()


if __name__ == '__main__':
    main()
