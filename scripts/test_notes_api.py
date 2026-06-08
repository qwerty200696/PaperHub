"""Quick test: verify notes API returns content from files"""
from __future__ import annotations

import os
import sys

# Clear proxy
for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    os.environ.pop(key, None)

sys.path.insert(0, "/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/backend")

from config import get_session, init_db, NOTES_DIR
from models import Note  # noqa: F401

init_db()
session = get_session()

# Test 1: Load a note and check to_dict() returns content
note = session.query(Note).filter(Note.id == 2).first()
if note:
    d = note.to_dict()
    content = d['content']
    filepath = NOTES_DIR / f"{note.id}.md"
    
    print(f"Note {note.id}: title='{note.title}'")
    print(f"  file exists: {filepath.exists()}")
    print(f"  content from file: {len(content)} chars")
    print(f"  content preview: {content[:100]}...")
    
    # Verify file matches
    file_content = filepath.read_text(encoding='utf-8')
    if content == file_content:
        print("  PASS: to_dict() content matches file")
    else:
        print("  FAIL: to_dict() content differs from file!")
    
    # Also check db content still there as fallback
    print(f"  db content len: {len(note.content)}")
else:
    print("Note id=2 not found!")

# Test 2: Verify all 24 notes have files
notes = session.query(Note).filter(Note.is_deleted == False).all()
all_good = True
for n in notes:
    fpath = NOTES_DIR / f"{n.id}.md"
    if not fpath.exists():
        print(f"  FAIL: {n.id} missing file")
        all_good = False
    else:
        fc = fpath.read_text(encoding='utf-8')
        d = n.to_dict()
        if d['content'] != fc:
            print(f"  FAIL: {n.id} to_dict() mismatch (db={len(str(n.content))}, file={len(fc)})")
            all_good = False

if all_good:
    print(f"\nAll {len(notes)} notes verified: PASS")
else:
    print(f"\nSome notes FAILED verification")

session.close()
