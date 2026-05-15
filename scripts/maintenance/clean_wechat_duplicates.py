"""
清理微信公众号文章的重复数据
保留最新创建的记录，删除其他重复项
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from backend.models import Article
from backend.config import get_session
from sqlalchemy import func


def clean_duplicate_wechat_articles(dry_run=True):
    """
    清理重复的微信公众号文章
    
    Args:
        dry_run: True=仅预览不实际删除，False=执行删除
    """
    session = get_session()
    
    print("=" * 80)
    if dry_run:
        print("🔍 [预览模式] 检查将要清理的重复数据")
    else:
        print("⚠️  [执行模式] 开始清理重复数据")
    print("=" * 80)
    
    # 查找所有URL重复的文章
    duplicate_groups = session.query(
        Article.url,
        func.count(Article.id).label('count')
    ).filter(
        Article.source == 'wechat',
        Article.url.isnot(None)
    ).group_by(
        Article.url
    ).having(
        func.count(Article.id) > 1
    ).all()
    
    if not duplicate_groups:
        print("\n✅ 没有发现需要清理的重复数据")
        session.close()
        return 0
    
    total_deleted = 0
    
    for url, count in duplicate_groups:
        print(f"\n{'─' * 80}")
        print(f"📄 URL: {url}")
        print(f"   重复数量: {count} 条")
        
        # 获取该URL的所有文章，按创建时间降序排列
        articles = session.query(Article).filter(
            Article.url == url,
            Article.source == 'wechat'
        ).order_by(
            Article.created_at.desc()
        ).all()
        
        # 保留第一条（最新的），删除其他
        keep_article = articles[0]
        delete_articles = articles[1:]
        
        print(f"\n   ✅ 保留 (ID: {keep_article.id}):")
        print(f"      标题: {keep_article.title[:60]}...")
        print(f"      创建时间: {keep_article.created_at}")
        print(f"      文件路径: {keep_article.file_path}")
        
        print(f"\n   ❌ 将删除 ({len(delete_articles)} 条):")
        for article in delete_articles:
            print(f"      - ID: {article.id}, 创建时间: {article.created_at}")
            
            if not dry_run:
                # 删除关联的标签关系
                session.execute(
                    Article.__table__.delete().where(Article.id == article.id)
                )
                total_deleted += 1
        
        if dry_run:
            print(f"\n   ℹ️  预览模式：未实际删除，将删除 {len(delete_articles)} 条记录")
        else:
            print(f"\n   ✅ 已删除 {len(delete_articles)} 条重复记录")
    
    # 提交事务
    if not dry_run and total_deleted > 0:
        session.commit()
        print(f"\n{'=' * 80}")
        print(f"✅ 清理完成！共删除 {total_deleted} 条重复记录")
        print(f"{'=' * 80}")
    elif dry_run:
        print(f"\n{'=' * 80}")
        print(f"ℹ️  预览结束。如需执行删除，请运行:")
        print(f"   python scripts/maintenance/clean_wechat_duplicates.py --execute")
        print(f"{'=' * 80}")
    
    session.close()
    return total_deleted


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='清理微信公众号文章重复数据')
    parser.add_argument('--execute', action='store_true', 
                       help='执行删除操作（默认仅预览）')
    
    args = parser.parse_args()
    
    dry_run = not args.execute
    clean_duplicate_wechat_articles(dry_run=dry_run)
