"""
P2 阶段数据库迁移脚本：为业务表添加 user_id / is_public 字段

执行方式：
    cd backend
    python ../scripts/migrate_p2_add_user_fields.py

迁移内容：
1. 为 papers / articles / notes / tags / wechat_subscriptions / wechat_config
   添加 user_id / is_public / created_by 三列（如不存在）
2. 创建 user_paper_status 表（如不存在）
3. 数据回填：
   - 若 users 表为空：创建一个默认 admin 用户（用户名 admin，密码 admin12345）
   - 将现有所有业务数据归属 admin 用户，并标记为公共（is_public=1）
4. 为现有 papers 数据初始化 user_paper_status 记录（继承原 starred 状态）

幂等性：本脚本可重复执行，已存在的列/表/数据会跳过。
"""
import os
import sys
from pathlib import Path

# 让脚本能从 backend/ 目录或项目根目录运行
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'backend'))


def main():
    from sqlalchemy import text, inspect
    from backend.config import get_engine, get_session, DB_DIR
    from backend.models import Base, User, Paper, Tag, Note, Article, WechatSubscription, WechatConfig, UserPaperStatus

    engine = get_engine()
    inspector = inspect(engine)

    print("=" * 60)
    print("PaperHub P2 迁移：添加多用户字段")
    print("=" * 60)
    print(f"数据库: {DB_DIR / 'paperhub.db'}")
    print()

    # ----------------------------------------------------------
    # 1. 确保 users 表存在（P1 阶段已建，此处兜底）
    # ----------------------------------------------------------
    Base.metadata.create_all(engine, tables=[User.__table__])
    print("[1/5] users 表已就绪")

    # ----------------------------------------------------------
    # 2. 为业务表添加 user_id / is_public / created_by 列
    # ----------------------------------------------------------
    business_tables = [
        'papers', 'articles', 'notes', 'tags',
        'wechat_subscriptions', 'wechat_config'
    ]
    new_columns = ['user_id', 'is_public', 'created_by']

    with engine.begin() as conn:
        for table_name in business_tables:
            if table_name not in inspector.get_table_names():
                print(f"  [跳过] 表 {table_name} 不存在")
                continue

            existing_cols = {c['name'] for c in inspector.get_columns(table_name)}
            for col_name in new_columns:
                if col_name in existing_cols:
                    continue
                # is_public 默认 0（False），迁移脚本会统一回填为 1
                if col_name == 'is_public':
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} BOOLEAN NOT NULL DEFAULT 0"
                elif col_name == 'user_id':
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} INTEGER"
                else:  # created_by
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col_name} INTEGER"
                conn.execute(text(sql))
                print(f"  [新增列] {table_name}.{col_name}")

            # 重建 inspector 以反映新列
            inspector = inspect(engine)

    print("[2/5] 业务表字段添加完成")

    # ----------------------------------------------------------
    # 3. 创建 user_paper_status 表
    # ----------------------------------------------------------
    Base.metadata.create_all(engine, tables=[UserPaperStatus.__table__])
    print("[3/5] user_paper_status 表已就绪")

    # ----------------------------------------------------------
    # 4. 数据回填：现有数据归属 admin 用户并标记公共
    # ----------------------------------------------------------
    session = get_session()
    try:
        # 4.1 确保至少有一个 admin 用户
        admin = session.query(User).filter_by(is_admin=True).first()
        if not admin:
            # users 表完全为空时创建默认 admin
            admin = User(
                username='admin',
                display_name='管理员',
                is_admin=True,
                is_active=True,
            )
            admin.set_password('admin12345')
            session.add(admin)
            session.commit()
            session.refresh(admin)
            print(f"[4/5] 创建默认管理员: admin / admin12345 (id={admin.id})")
        else:
            print(f"[4/5] 使用现有管理员: {admin.username} (id={admin.id})")

        admin_id = admin.id

        # 4.2 将所有 user_id IS NULL 的业务数据归属 admin，并标记为公共
        inspector = inspect(engine)
        for table_name in business_tables:
            # 跳过不存在的表（如测试环境只创建了部分表）
            if table_name not in inspector.get_table_names():
                continue
            result = session.execute(text(
                f"UPDATE {table_name} SET user_id = :uid, is_public = 1, created_by = :uid "
                f"WHERE user_id IS NULL"
            ), {'uid': admin_id})
            if result.rowcount > 0:
                print(f"  [回填] {table_name}: {result.rowcount} 行 -> admin (公共)")
        session.commit()
    finally:
        session.close()

    # ----------------------------------------------------------
    # 5. 为现有 papers 初始化 user_paper_status（继承原 starred）
    # ----------------------------------------------------------
    inspector = inspect(engine)
    if 'papers' not in inspector.get_table_names() or 'user_paper_status' not in inspector.get_table_names():
        print("[5/5] 跳过 user_paper_status 初始化（papers 或 user_paper_status 表不存在）")
        return

    session = get_session()
    try:
        # 查找所有没有对应 user_paper_status 记录的 (paper, admin) 组合
        rows = session.execute(text("""
            SELECT p.id, p.starred, p.user_id
            FROM papers p
            LEFT JOIN user_paper_status ups
              ON ups.paper_id = p.id AND ups.user_id = p.user_id
            WHERE ups.id IS NULL AND p.user_id IS NOT NULL
        """)).fetchall()

        inserted = 0
        for paper_id, starred, user_id in rows:
            session.execute(text("""
                INSERT INTO user_paper_status
                    (user_id, paper_id, starred, read_status, read_progress, created_at, updated_at)
                VALUES
                    (:uid, :pid, :starred, 'unread', 0, datetime('now'), datetime('now'))
            """), {'uid': user_id, 'pid': paper_id, 'starred': 1 if starred else 0})
            inserted += 1

        session.commit()
        print(f"[5/5] 初始化 user_paper_status: {inserted} 条记录")
    finally:
        session.close()

    print()
    print("=" * 60)
    print("✅ P2 迁移完成")
    print()
    print("后续步骤：")
    print("  - P3 阶段：业务 API 加 @auth_required 装饰器 + user_id 过滤")
    print("  - 启用强制鉴权：设置环境变量 ENFORCE_AUTH=1")
    print("=" * 60)


if __name__ == '__main__':
    main()
