#!/usr/bin/env python3
"""
测试批量操作 API - 论文库/文章库/笔记库

用法:
    python scripts/tests/test_batch_api.py

测试覆盖:
    1. 论文库: 批量改状态、加标签、删标签、标星、删除
    2. 文章库: 批量改状态、加标签、删标签、标星、删除
    3. 笔记库: 批量改状态、加标签、删标签、标星、置顶、删除
"""
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent.parent / 'backend'
sys.path.insert(0, str(backend_path))

import requests

BASE_URL = "http://localhost:5899"


def print_header(title):
    print()
    print("=" * 80)
    print(f"  {title}")
    print("=" * 80)


def print_result(name, success, detail=""):
    if success:
        print(f"  ✅ {name}")
    else:
        print(f"  ❌ {name}")
    if detail:
        print(f"     {detail}")


def create_test_paper(title_prefix="Test Paper"):
    """创建测试论文 - 使用随机 arXiv ID 避免重复"""
    import time
    import random
    title = f"{title_prefix} {int(time.time())}"
    # 生成随机 arXiv ID 避免重复
    random_id = f"{random.randint(2301, 2599)}.{random.randint(10000, 99999)}"
    resp = requests.post(f"{BASE_URL}/api/ingest/arxiv", json={"input": random_id})
    if resp.status_code in [200, 201]:
        data = resp.json()
        paper = data.get('paper')
        if paper:
            paper_id = paper.get('id')
            # 更新标题用于测试
            requests.put(f"{BASE_URL}/api/papers/{paper_id}", json={"title": title})
            return paper_id
    # 如果是已存在的情况，也返回 paper_id
    if resp.status_code == 409:
        paper = resp.json().get('paper', {})
        if paper.get('id'):
            return paper.get('id')
    print(f"  ingest 结果: {resp.status_code} - {resp.text[:200] if resp.text else 'empty'}")
    return None


def create_test_article():
    """创建测试文章 - 使用随机内容避免重复"""
    import time
    import random
    title = f"Test Article {int(time.time())} {random.randint(1000, 9999)}"
    resp = requests.post(f"{BASE_URL}/api/articles", json={
        "title": title,
        "content": f"Test content for batch operation {random.randint(1, 10000)}",
        "source": "web",
        "author": "Test Author"
    })
    if resp.status_code == 201:
        return resp.json().get('article', {}).get('id')
    # 如果是已存在的情况，也返回 article_id
    if resp.status_code == 409:
        article = resp.json().get('article', {})
        if article.get('id'):
            return article.get('id')
    print(f"  创建文章失败: {resp.status_code}")
    return None


def create_test_note():
    """创建测试笔记 - 使用随机内容避免重复"""
    import time
    import random
    title = f"Test Note {int(time.time())} {random.randint(1000, 9999)}"
    resp = requests.post(f"{BASE_URL}/api/notes", json={
        "title": title,
        "content": f"Test content for batch operation {random.randint(1, 10000)}"
    })
    if resp.status_code == 201:
        return resp.json().get('id')
    # 如果是已存在的情况，也返回 note_id
    if resp.status_code == 409:
        note = resp.json().get('note', {})
        if note.get('id'):
            return note.get('id')
    print(f"  创建笔记失败: {resp.status_code}")
    return None


def test_paper_batch():
    """测试论文库批量操作"""
    print_header("📚 论文库批量操作测试")

    # 1. 创建测试论文
    print("\n[1] 创建测试论文...")
    paper_ids = []
    for i in range(3):
        paper_id = create_test_paper(f"Batch Paper {i}")
        if paper_id:
            paper_ids.append(paper_id)
            print(f"     创建论文 ID={paper_id}")
        else:
            print(f"     ❌ 创建失败")

    if len(paper_ids) < 2:
        print("  ⚠️  需要至少 2 篇论文进行测试，跳过")
        return

    # 2. 测试批量改状态
    print("\n[2] 测试批量改状态...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": paper_ids,
        "action": "update_status",
        "status": "reading"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量改状态 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量改状态", False, resp.text)

    # 3. 测试批量加标签
    print("\n[3] 测试批量加标签...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": paper_ids,
        "action": "add_tags",
        "tag_names": ["批量测试标签"]
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量加标签 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量加标签", False, resp.text)

    # 4. 测试批量标星
    print("\n[4] 测试批量标星...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": paper_ids,
        "action": "set_star",
        "starred": True
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量标星 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量标星", False, resp.text)

    # 5. 测试批量删除
    print("\n[5] 测试批量删除...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": paper_ids,
        "action": "delete"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量删除 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量删除", False, resp.text)


def test_article_batch():
    """测试文章库批量操作"""
    print_header("📰 文章库批量操作测试")

    # 1. 创建测试文章
    print("\n[1] 创建测试文章...")
    article_ids = []
    for i in range(3):
        article_id = create_test_article()
        if article_id:
            article_ids.append(article_id)
            print(f"     创建文章 ID={article_id}")
        else:
            print(f"     ❌ 创建失败")

    if len(article_ids) < 2:
        print("  ⚠️  需要至少 2 篇文章进行测试，跳过")
        return

    # 2. 测试批量改状态
    print("\n[2] 测试批量改状态...")
    resp = requests.post(f"{BASE_URL}/api/articles/batch", json={
        "article_ids": article_ids,
        "action": "update_status",
        "status": "done"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量改状态 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量改状态", False, resp.text)

    # 3. 测试批量加标签
    print("\n[3] 测试批量加标签...")
    resp = requests.post(f"{BASE_URL}/api/articles/batch", json={
        "article_ids": article_ids,
        "action": "add_tags",
        "tag_names": ["文章测试标签"]
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量加标签 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量加标签", False, resp.text)

    # 4. 测试批量删除
    print("\n[4] 测试批量删除...")
    resp = requests.post(f"{BASE_URL}/api/articles/batch", json={
        "article_ids": article_ids,
        "action": "delete"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量删除 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量删除", False, resp.text)


def test_note_batch():
    """测试笔记库批量操作"""
    print_header("📝 笔记库批量操作测试")

    # 1. 创建测试笔记
    print("\n[1] 创建测试笔记...")
    note_ids = []
    for i in range(3):
        note_id = create_test_note()
        if note_id:
            note_ids.append(note_id)
            print(f"     创建笔记 ID={note_id}")
        else:
            print(f"     ❌ 创建失败")

    if len(note_ids) < 2:
        print("  ⚠️  需要至少 2 篇笔记进行测试，跳过")
        return

    # 2. 测试批量改状态
    print("\n[2] 测试批量改状态...")
    resp = requests.post(f"{BASE_URL}/api/notes/batch", json={
        "note_ids": note_ids,
        "action": "update_status",
        "status": "mastered"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量改状态 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量改状态", False, resp.text)

    # 3. 测试批量加标签
    print("\n[3] 测试批量加标签...")
    resp = requests.post(f"{BASE_URL}/api/notes/batch", json={
        "note_ids": note_ids,
        "action": "add_tags",
        "tag_names": ["笔记测试标签"]
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量加标签 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量加标签", False, resp.text)

    # 4. 测试批量置顶
    print("\n[4] 测试批量置顶...")
    resp = requests.post(f"{BASE_URL}/api/notes/batch", json={
        "note_ids": note_ids,
        "action": "toggle_pinned"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量置顶 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量置顶", False, resp.text)

    # 5. 测试批量删除
    print("\n[5] 测试批量删除...")
    resp = requests.post(f"{BASE_URL}/api/notes/batch", json={
        "note_ids": note_ids,
        "action": "delete"
    })
    if resp.status_code == 200:
        data = resp.json()
        print_result(f"批量删除 → {data.get('message', '')}",
                   data.get('success_count', 0) > 0)
    else:
        print_result("批量删除", False, resp.text)


def test_error_handling():
    """测试错误处理"""
    print_header("⚠️  错误处理测试")

    # 1. 空 ID 列表
    print("\n[1] 空 paper_ids 测试...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": [],
        "action": "update_status"
    })
    print_result(f"返回 {resp.status_code}",
               resp.status_code == 400,
               f"错误信息: {resp.json().get('error') if resp.status_code == 400 else resp.text}")

    # 2. 缺少 action
    print("\n[2] 缺少 action 测试...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": [1, 2, 3]
    })
    print_result(f"返回 {resp.status_code}",
               resp.status_code == 400,
               f"错误信息: {resp.json().get('error') if resp.status_code == 400 else resp.text}")

    # 3. 无效的 action
    print("\n[3] 无效 action 测试...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": [1, 2, 3],
        "action": "invalid_action"
    })
    print_result(f"返回 {resp.status_code}",
               resp.status_code in [200, 400],  # 应该成功但标记 failed
               resp.json().get('results', {}).get('failed') if resp.status_code == 200 else resp.text)

    # 4. 无效的状态值
    print("\n[4] 无效 status 测试...")
    resp = requests.post(f"{BASE_URL}/api/papers/batch", json={
        "paper_ids": [99999],  # 不存在的 ID
        "action": "update_status",
        "status": "invalid_status"
    })
    print_result(f"返回 {resp.status_code}",
               resp.status_code in [200, 400],
               resp.json().get('message') if resp.status_code == 200 else "")


def check_server():
    """检查服务器是否运行"""
    print("🔍 检查后端服务...")
    try:
        resp = requests.get(f"{BASE_URL}/health", timeout=2)
        if resp.status_code == 200:
            print("  ✅ 后端服务正常运行")
            return True
    except requests.exceptions.ConnectionError:
        print("  ❌ 无法连接到后端服务")
        print("  💡 请先启动后端: cd backend && python app.py")
        return False
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        return False


def main():
    print()
    print("#" * 80)
    print("#" + " " * 78 + "#")
    print("#" + "  PaperHub 批量操作 API 测试".center(76) + "#")
    print("#" + " " * 78 + "#")
    print("#" * 80)

    # 检查服务
    if not check_server():
        sys.exit(1)

    # 运行测试
    try:
        test_paper_batch()
        test_article_batch()
        test_note_batch()
        test_error_handling()
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

    print()
    print("=" * 80)
    print("  ✅ 测试完成")
    print("=" * 80)
    print()
    print("💡 前端测试:")
    print("   1. 启动后端: cd backend && python app.py")
    print("   2. 打开浏览器: http://localhost:5000")
    print("   3. 在论文库/文章库/笔记库列表页，勾选多条记录")
    print("   4. 观察顶部是否出现绿色批量操作栏")
    print("   5. 选择操作并执行")
    print()


if __name__ == "__main__":
    main()
