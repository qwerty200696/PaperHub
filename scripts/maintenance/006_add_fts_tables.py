"""SQLite FTS5 全文检索表迁移脚本"""

import os
import sys
import sqlite3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config, DB_DIR

DATABASE_PATH = str(DB_DIR / "paperhub.db")

def create_fts_tables():
    """创建 FTS5 虚拟表和触发器"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 创建论文全文检索表
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS papers_fts USING fts5(
            title,
            abstract,
            authors,
            category,
            tokenize='unicode61'
        )
    ''')
    
    # 创建文章全文检索表
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS articles_fts USING fts5(
            title,
            content,
            author,
            source,
            tokenize='unicode61'
        )
    ''')
    
    # 创建笔记全文检索表
    cursor.execute('''
        CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts USING fts5(
            title,
            content,
            source,
            tokenize='unicode61'
        )
    ''')
    
    # 删除已存在的触发器（避免重复创建）
    cursor.execute("DROP TRIGGER IF EXISTS papers_insert")
    cursor.execute("DROP TRIGGER IF EXISTS papers_update")
    cursor.execute("DROP TRIGGER IF EXISTS papers_delete")
    
    # 论文表触发器
    cursor.execute('''
        CREATE TRIGGER papers_insert AFTER INSERT ON papers
        BEGIN
            INSERT INTO papers_fts(rowid, title, abstract, authors, category)
            VALUES (new.id, new.title, new.abstract, new.authors, new.category_l1);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER papers_update AFTER UPDATE ON papers
        BEGIN
            DELETE FROM papers_fts WHERE rowid = old.id;
            INSERT INTO papers_fts(rowid, title, abstract, authors, category)
            VALUES (new.id, new.title, new.abstract, new.authors, new.category_l1);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER papers_delete AFTER DELETE ON papers
        BEGIN
            DELETE FROM papers_fts WHERE rowid = old.id;
        END
    ''')
    
    # 删除已存在的文章触发器
    cursor.execute("DROP TRIGGER IF EXISTS articles_insert")
    cursor.execute("DROP TRIGGER IF EXISTS articles_update")
    cursor.execute("DROP TRIGGER IF EXISTS articles_delete")
    
    # 文章表触发器
    cursor.execute('''
        CREATE TRIGGER articles_insert AFTER INSERT ON articles
        BEGIN
            INSERT INTO articles_fts(rowid, title, content, author, source)
            VALUES (new.id, new.title, new.content, new.author, new.source);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER articles_update AFTER UPDATE ON articles
        BEGIN
            DELETE FROM articles_fts WHERE rowid = old.id;
            INSERT INTO articles_fts(rowid, title, content, author, source)
            VALUES (new.id, new.title, new.content, new.author, new.source);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER articles_delete AFTER DELETE ON articles
        BEGIN
            DELETE FROM articles_fts WHERE rowid = old.id;
        END
    ''')
    
    # 删除已存在的笔记触发器
    cursor.execute("DROP TRIGGER IF EXISTS notes_insert")
    cursor.execute("DROP TRIGGER IF EXISTS notes_update")
    cursor.execute("DROP TRIGGER IF EXISTS notes_delete")
    
    # 笔记表触发器
    cursor.execute('''
        CREATE TRIGGER notes_insert AFTER INSERT ON notes
        BEGIN
            INSERT INTO notes_fts(rowid, title, content, source)
            VALUES (new.id, new.title, new.content, new.source);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER notes_update AFTER UPDATE ON notes
        BEGIN
            DELETE FROM notes_fts WHERE rowid = old.id;
            INSERT INTO notes_fts(rowid, title, content, source)
            VALUES (new.id, new.title, new.content, new.source);
        END
    ''')
    
    cursor.execute('''
        CREATE TRIGGER notes_delete AFTER DELETE ON notes
        BEGIN
            DELETE FROM notes_fts WHERE rowid = old.id;
        END
    ''')
    
    conn.commit()
    conn.close()
    print("✅ FTS5 虚拟表和触发器创建成功")

def init_fts_data():
    """初始化 FTS 表数据（同步现有数据）"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # 清空现有 FTS 数据
    cursor.execute("DELETE FROM papers_fts")
    cursor.execute("DELETE FROM articles_fts")
    cursor.execute("DELETE FROM notes_fts")
    
    # 同步论文数据
    cursor.execute('''
        INSERT INTO papers_fts(rowid, title, abstract, authors, category)
        SELECT id, title, abstract, authors, category_l1 FROM papers
    ''')
    
    # 同步文章数据
    cursor.execute('''
        INSERT INTO articles_fts(rowid, title, content, author, source)
        SELECT id, title, content, author, source FROM articles
    ''')
    
    # 同步笔记数据
    cursor.execute('''
        INSERT INTO notes_fts(rowid, title, content, source)
        SELECT id, title, content, source FROM notes
    ''')
    
    conn.commit()
    conn.close()
    print("✅ FTS 表数据初始化成功")

if __name__ == '__main__':
    create_fts_tables()
    init_fts_data()
    print("\n🎉 SQLite FTS5 全文检索表迁移完成！")