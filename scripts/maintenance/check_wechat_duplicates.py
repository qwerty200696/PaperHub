"""
检查微信公众号文章是否有重复数据
"""
import sys
import os

# 添加项目根目录到路径
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, project_root)

from backend.models import Article
from backend.config import get_session
from sqlalchemy import func


def check_duplicate_wechat_articles():
    """检查重复的微信公众号文章"""
    session = get_session()
    
    print("=" * 80)
    print("🔍 检查微信公众号文章重复数据")
    print("=" * 80)
    
    # 1. 统计总数
    total_count = session.query(Article).filter_by(source='wechat').count()
    print(f"\n📊 微信公众号文章总数: {total_count}")
    
    # 2. 按URL分组检查重复
    duplicate_by_url = session.query(
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
    
    if duplicate_by_url:
        print(f"\n⚠️  发现 {len(duplicate_by_url)} 个URL重复的文章:")
        print("-" * 80)
        for url, count in duplicate_by_url:
            print(f"\nURL: {url}")
            print(f"重复次数: {count}")
            
            # 获取该URL的所有文章详情
            articles = session.query(Article).filter(
                Article.url == url,
                Article.source == 'wechat'
            ).all()
            
            for i, article in enumerate(articles, 1):
                print(f"  [{i}] ID: {article.id}")
                print(f"      标题: {article.title[:50]}...")
                print(f"      作者: {article.author}")
                print(f"      发布时间: {article.published_at}")
                print(f"      创建时间: {article.created_at}")
                print(f"      文件路径: {article.file_path}")
                print(f"      状态: {article.status}")
    else:
        print("\n✅ 没有发现URL重复的文章")
    
    # 3. 按标题分组检查重复（可能URL不同但内容相同）
    duplicate_by_title = session.query(
        Article.title,
        func.count(Article.id).label('count')
    ).filter(
        Article.source == 'wechat',
        Article.title.isnot(None)
    ).group_by(
        Article.title
    ).having(
        func.count(Article.id) > 1
    ).all()
    
    if duplicate_by_title:
        print(f"\n⚠️  发现 {len(duplicate_by_title)} 个标题重复的文章:")
        print("-" * 80)
        for title, count in duplicate_by_title[:10]:  # 只显示前10个
            print(f"\n标题: {title[:60]}...")
            print(f"重复次数: {count}")
            
            articles = session.query(Article).filter(
                Article.title == title,
                Article.source == 'wechat'
            ).all()
            
            for i, article in enumerate(articles, 1):
                print(f"  [{i}] ID: {article.id}")
                print(f"      URL: {article.url}")
                print(f"      发布时间: {article.published_at}")
                print(f"      创建时间: {article.created_at}")
    else:
        print("\n✅ 没有发现标题重复的文章")
    
    # 4. 检查file_path重复
    duplicate_by_path = session.query(
        Article.file_path,
        func.count(Article.id).label('count')
    ).filter(
        Article.source == 'wechat',
        Article.file_path.isnot(None)
    ).group_by(
        Article.file_path
    ).having(
        func.count(Article.id) > 1
    ).all()
    
    if duplicate_by_path:
        print(f"\n⚠️  发现 {len(duplicate_by_path)} 个文件路径重复的文章:")
        print("-" * 80)
        for file_path, count in duplicate_by_path:
            print(f"\n文件路径: {file_path}")
            print(f"重复次数: {count}")
            
            articles = session.query(Article).filter(
                Article.file_path == file_path,
                Article.source == 'wechat'
            ).all()
            
            for i, article in enumerate(articles, 1):
                print(f"  [{i}] ID: {article.id}")
                print(f"      标题: {article.title[:50]}...")
                print(f"      URL: {article.url}")
                print(f"      创建时间: {article.created_at}")
    else:
        print("\n✅ 没有发现文件路径重复的文章")
    
    # 5. 总结
    print("\n" + "=" * 80)
    print("📋 检查总结")
    print("=" * 80)
    
    has_duplicates = duplicate_by_url or duplicate_by_title or duplicate_by_path
    
    if has_duplicates:
        print("\n❌ 发现重复数据！建议清理重复项。")
        print("\n💡 清理建议:")
        print("   1. 保留最新创建时间的记录")
        print("   2. 删除其他重复记录")
        print("   3. 运行去重脚本: python scripts/maintenance/cleanup_data.py")
    else:
        print("\n✅ 未发现重复数据，数据库状态良好！")
    
    session.close()
    return has_duplicates


if __name__ == '__main__':
    check_duplicate_wechat_articles()
