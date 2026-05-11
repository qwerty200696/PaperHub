#!/usr/bin/env python3
"""
批量操作前后端测试指南

本文档说明如何测试 PaperHub 新增的批量操作功能。
"""

# ============================================================================
# 后端 API 测试
# ============================================================================

## 运行后端测试脚本

```bash
cd /Users/wanglijie/PycharmProjects/claude_code_project/PaperHub
python scripts/tests/test_batch_api.py
```

## API 端点说明

### 论文库批量操作
POST /api/papers/batch

请求体:
{
    "paper_ids": [1, 2, 3],
    "action": "update_status" | "add_tags" | "remove_tags" | "toggle_star" | "set_star" | "delete",
    "status": "pending" | "reading" | "done" | "mastered",  # update_status 使用
    "tag_names": ["LLM", "RAG"],  # add_tags / remove_tags 使用
    "starred": true | false  # set_star 使用
}

响应:
{
    "message": "Batch operation completed: 3 success, 0 failed",
    "action": "update_status",
    "success_count": 3,
    "failed_count": 0,
    "results": {"success": [1, 2, 3], "failed": []}
}

### 文章库批量操作
POST /api/articles/batch

请求体: 同论文库，将 paper_ids 改为 article_ids

### 笔记库批量操作
POST /api/notes/batch

请求体: 同论文库，将 paper_ids 改为 note_ids
额外 action:
    - "toggle_pinned": 切换置顶状态

## 手动测试命令示例

```bash
# 假设有 ID 为 1, 2, 3 的论文

# 批量改状态为"在读"
curl -X POST http://localhost:5000/api/papers/batch \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": [1, 2, 3], "action": "update_status", "status": "reading"}'

# 批量添加标签
curl -X POST http://localhost:5000/api/papers/batch \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": [1, 2, 3], "action": "add_tags", "tag_names": ["LLM"]}'

# 批量标星
curl -X POST http://localhost:5000/api/papers/batch \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": [1, 2, 3], "action": "set_star", "starred": true}'

# 批量删除（需要确认）
curl -X POST http://localhost:5000/api/papers/batch \
  -H "Content-Type: application/json" \
  -d '{"paper_ids": [1, 2, 3], "action": "delete"}'
```


# ============================================================================
# 前端测试
# ============================================================================

## 测试步骤

### 1. 论文库批量操作

1. 启动后端服务
   ```bash
   cd backend && python app.py
   ```

2. 打开浏览器访问 http://localhost:5000

3. 进入「论文库」页面

4. 在列表左侧勾选 2-3 条论文

5. 观察：
   - 论文标题左侧出现绿色批量操作栏
   - 显示「已选 N 篇」
   - 显示操作类型下拉框

6. 测试各种操作：
   - 「改状态」→ 选择「在读」→ 点击「执行」
   - 「加标签」→ 输入「测试标签」→ 点击「执行」
   - 「标星」→ 点击「执行」
   - 「批量删除」→ 确认删除

### 2. 文章库批量操作

1. 进入「文章库」页面

2. 勾选 2-3 篇文章

3. 观察批量操作栏出现

4. 测试各种操作

### 3. 笔记库批量操作

1. 进入「笔记库」页面

2. 勾选 2-3 篇笔记

3. 观察批量操作栏（包含「置顶」选项）

4. 测试各种操作


# ============================================================================
# 预期结果
# ============================================================================

## 成功操作
- ✅ 批量改状态后，所有选中论文/文章/笔记的状态同步更新
- ✅ 批量加标签后，标签正确添加到所有选中项
- ✅ 批量标星后，所有选中项均标星
- ✅ 批量删除后，所有选中项及其关联文件被删除

## 错误处理
- ❌ 未选择任何项时，显示警告提示
- ❌ 未选择操作类型时，显示警告提示
- ❌ 批量删除时，弹出确认对话框
- ❌ 删除不存在的项时，该项标记为 failed，不影响其他项

## UI 表现
- ✅ 选中项时，批量操作栏以绿色背景显示
- ✅ 执行完成后，操作栏自动隐藏
- ✅ 数据列表自动刷新
