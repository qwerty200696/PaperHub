#!/usr/bin/env python3
"""
清理 PaperHub 数据目录中的冗余文件

规则：
1. 如果数据库中 save_local=False 但 file_path 不为空，则删除该文件并清空 file_path
2. 如果文件在磁盘上存在但数据库中没有记录，则删除该文件

支持的类型：
- 论文（papers）：PDF 文件
- 文章（articles）：HTML 文件
- 笔记（notes）：MD 文件

特殊处理：
- 知乎/微信文章会同时保存 HTML 和 MD 文件，MD 文件不算冗余
- 笔记导入时会同时保存 .md 和 .html 文件，.md 文件不算冗余

使用方法：
    python cleanup_data.py          # 查看冗余文件（不删除）
    python cleanup_data.py --dry     # 查看冗余文件（不删除）
    python cleanup_data.py --remove # 删除冗余文件
"""

import os
import sys
import requests
from pathlib import Path

# API 配置
API_BASE = "http://localhost:5899/api"

# 数据目录配置
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
PAPERS_BASE_DIR = DATA_DIR.parent  # PaperHub 根目录


def get_all_papers():
    """从 API 获取所有论文"""
    try:
        response = requests.get(f"{API_BASE}/papers", timeout=10)
        response.raise_for_status()
        return response.json()['papers']
    except Exception as e:
        print(f"❌ 获取论文列表失败: {e}")
        sys.exit(1)


def get_all_articles():
    """从 API 获取所有文章"""
    try:
        response = requests.get(f"{API_BASE}/articles", timeout=10)
        response.raise_for_status()
        return response.json().get('articles', [])
    except Exception as e:
        print(f"❌ 获取文章列表失败: {e}")
        return []


def get_all_notes():
    """从 API 获取所有笔记"""
    try:
        response = requests.get(f"{API_BASE}/notes", timeout=10)
        response.raise_for_status()
        return response.json().get('notes', [])
    except Exception as e:
        print(f"❌ 获取笔记列表失败: {e}")
        return []


def get_all_db_file_paths(papers, articles, notes):
    """获取数据库中所有类型的 file_path"""
    db_paths = set()

    # 添加论文的文件路径
    for paper in papers:
        if paper.get('file_path'):
            db_paths.add(paper['file_path'])

    # 添加文章的文件路径
    for article in articles:
        if article.get('file_path'):
            db_paths.add(article['file_path'])

    # 添加笔记的文件路径
    for note in notes:
        if note.get('file_path'):
            db_paths.add(note['file_path'])

    return db_paths


def find_inconsistent_items(papers, articles, notes):
    """找出 save_local=False 但 file_path 不为空的项"""
    inconsistent = []

    # 检查论文
    for paper in papers:
        if paper.get('save_local') == False and paper.get('file_path'):
            inconsistent.append({
                'type': 'paper',
                'id': paper['id'],
                'title': (paper.get('title') or '')[:50],
                'file_path': paper['file_path']
            })

    # 检查文章
    for article in articles:
        if article.get('save_local') == False and article.get('file_path'):
            inconsistent.append({
                'type': 'article',
                'id': article['id'],
                'title': (article.get('title') or '')[:50],
                'file_path': article['file_path']
            })

    return inconsistent


def find_orphaned_files(db_paths):
    """找出磁盘上存在但数据库中没有记录的文件"""
    orphaned = []

    # 支持的文件扩展名
    extensions = {'.pdf', '.html', '.htm', '.md', '.txt'}

    # 检查数据目录是否存在
    if not DATA_DIR.exists():
        return orphaned

    # 遍历数据目录
    for subdir in DATA_DIR.iterdir():
        if not subdir.is_dir():
            continue

        # 递归查找所有文件
        for file_path in subdir.rglob("*"):
            if not file_path.is_file():
                continue

            # 检查扩展名
            if file_path.suffix.lower() not in extensions:
                continue

            # 转换为与数据库一致的路径格式 (data/xxx)
            try:
                relative_path = str(file_path.relative_to(PAPERS_BASE_DIR))
            except ValueError:
                continue

            # ==============================================
            # 特殊处理：配对的 md 文件
            # ==============================================
            # 有些文件会同时保存 HTML 和 MD 文件，需要检查配对情况
            is_paired_md = False
            if file_path.suffix.lower() == '.md':
                parent_dir = file_path.parent.name

                # 知乎/微信文章的 md 文件（配对 HTML）
                if parent_dir in ['zhihu', 'wechat']:
                    html_path = file_path.with_suffix('.html')
                    html_relative = str(html_path.relative_to(PAPERS_BASE_DIR))
                    if html_relative in db_paths:
                        is_paired_md = True

                # 笔记目录的 md 文件（配对 HTML）
                # 笔记导入时会同时保存 .md 和 .html 文件
                elif parent_dir == 'notes':
                    html_path = file_path.with_suffix('.html')
                    html_relative = str(html_path.relative_to(PAPERS_BASE_DIR))
                    if html_relative in db_paths:
                        is_paired_md = True

            # 如果是配对的 md 文件，跳过
            if is_paired_md:
                continue
            # ==============================================

            # 检查是否在数据库中
            if relative_path not in db_paths:
                orphaned.append({
                    'path': str(file_path),
                    'relative_path': relative_path,
                    'size': file_path.stat().st_size
                })

    return orphaned


def format_size(size_bytes):
    """格式化文件大小为人类可读格式"""
    if size_bytes < 0:
        return "0B"
    elif size_bytes < 1024:
        return f"{size_bytes}B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f}KB"
    else:
        return f"{size_bytes / (1024 * 1024):.1f}MB"


def print_report(orphaned_files, inconsistent_items):
    """打印清理报告"""
    total_size = sum(f['size'] for f in orphaned_files)

    print("\n" + "=" * 60)
    print("📊 PaperHub 数据清理报告")
    print("=" * 60)

    # 显示不一致的项
    print(f"\n🔴 save_local=False 但 file_path 不为空 ({len(inconsistent_items)} 个):")
    if inconsistent_items:
        for item in inconsistent_items:
            type_emoji = {"paper": "📚", "article": "📰", "note": "📝"}.get(item['type'], "📄")
            print(f"   {type_emoji} [{item['type']}] ID={item['id']}: {item['title']}...")
            print(f"         file_path: {item['file_path']}")
    else:
        print("   ✅ 没有不一致的项")

    # 显示孤立的文件
    print(f"\n🟡 磁盘上有但数据库中没有 ({len(orphaned_files)} 个, {format_size(total_size)}):")
    if orphaned_files:
        for f in orphaned_files[:20]:
            print(f"   - {f['relative_path']} ({format_size(f['size'])})")
        if len(orphaned_files) > 20:
            print(f"   ... 还有 {len(orphaned_files) - 20} 个文件")
    else:
        print("   ✅ 没有孤立的文件")

    print("\n" + "=" * 60)

    return total_size


def remove_orphaned_files(orphaned_files, inconsistent_items):
    """删除冗余文件"""
    removed_count = 0
    removed_size = 0

    # 处理不一致的项
    for item in inconsistent_items:
        file_path = Path(item['file_path'])
        if not file_path.is_absolute():
            file_path = PAPERS_BASE_DIR / file_path

        # 删除文件
        if file_path.exists():
            try:
                file_size = file_path.stat().st_size
                file_path.unlink()
                print(f"✅ 已删除: {item['file_path']}")
                removed_count += 1
                removed_size += file_size
            except Exception as e:
                print(f"❌ 删除失败 {item['file_path']}: {e}")

        # 清空数据库记录
        try:
            api_path = f"{API_BASE}/{item['type']}s/{item['id']}"
            response = requests.put(
                api_path,
                json={'file_path': None},
                timeout=10
            )
            if response.ok:
                print(f"   📝 已清空数据库记录: [{item['type']}] ID={item['id']}")
        except Exception as e:
            print(f"   ⚠️ 清空数据库记录失败: {e}")

    # 处理孤立文件
    for f in orphaned_files:
        try:
            Path(f['path']).unlink()
            print(f"✅ 已删除: {f['relative_path']}")
            removed_count += 1
            removed_size += f['size']
        except Exception as e:
            print(f"❌ 删除失败 {f['relative_path']}: {e}")

    return removed_count, removed_size


def main():
    """主函数"""
    # 解析命令行参数
    dry_run = "--dry" in sys.argv or ("--remove" not in sys.argv and "--dry" not in sys.argv)
    remove = "--remove" in sys.argv

    print("🔍 正在扫描数据...")

    # 获取所有数据
    papers = get_all_papers()
    articles = get_all_articles()
    notes = get_all_notes()

    # 输出统计信息
    print(f"📚 论文: {len(papers)} 篇")
    print(f"📰 文章: {len(articles)} 篇")
    print(f"📝 笔记: {len(notes)} 篇")

    # 获取数据库中的文件路径
    db_paths = get_all_db_file_paths(papers, articles, notes)
    print(f"📁 数据库中记录的文件路径: {len(db_paths)} 个")

    # 查找问题文件
    inconsistent_items = find_inconsistent_items(papers, articles, notes)
    orphaned_files = find_orphaned_files(db_paths)

    # 打印报告
    print_report(orphaned_files, inconsistent_items)

    # 执行删除操作
    if remove:
        print("\n🗑️  开始删除冗余文件...")
        removed_count, removed_size = remove_orphaned_files(orphaned_files, inconsistent_items)
        print(f"\n✅ 已删除 {removed_count} 个文件，共 {format_size(removed_size)}")
    elif dry_run:
        print("\n💡 这是预览模式，未删除任何文件")
        print("   使用 --remove 参数来删除文件")

    print()


if __name__ == "__main__":
    main()
