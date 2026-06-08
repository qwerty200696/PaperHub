"""迁移现有 DB 笔记内容到本地 Markdown 文件"""
from __future__ import annotations

import os
import sys

# Clear broken proxy
for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(key, None)

BASE_DIR = "/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub"
sys.path.insert(0, os.path.join(BASE_DIR, "backend"))

from config import get_session, init_db, NOTES_DIR
from models import Note

init_db()
session = get_session()

notes: list[Note] = session.query(Note).filter(Note.is_deleted == False).all()
print(f"Total non-deleted notes: {len(notes)}")

deleted_count: int = session.query(Note).filter(Note.is_deleted == True).count()
print(f"Deleted notes (will be skipped): {deleted_count}")

migrated = 0
skipped = 0
for note in notes:
    content: str = str(note.content or "")
    if not content.strip():
        title_preview = (note.title or "(no title)")[:60]
        print(f"  [{note.id}] SKIPPED (empty content): {title_preview}")
        skipped += 1
        continue

    filepath = NOTES_DIR / f"{note.id}.md"
    filepath.write_text(content, encoding="utf-8")
    print(f"  [{note.id}] MIGRATED ({len(content)} chars) -> {filepath.name}")
    migrated += 1

session.close()
print(f"\n=== Done: {migrated} migrated, {skipped} skipped ===")
