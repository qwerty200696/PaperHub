#!/usr/bin/env python3
# -*- coding: utf-8 -*-

with open('/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/docs/笔记系统设计方案.md', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 更新设计理念
old_design = """# 笔记系统设计方案

---

## 一、设计理念

笔记是独立实体（Note），与论文（Paper）多对多关联。
- 一篇笔记可以关联 0 到 N 篇论文
- 一篇论文可以有 0 到 N 篇笔记
- 对话笔记迁移后成为 Note，与新笔记系统完全兼容"""

new_design = """# PaperHub 笔记与文章系统设计方案

---

## 一、设计理念

PaperHub 采用**三层内容库**架构：

| 内容类型 | 存储位置 | 说明 |
|---------|---------|------|
| 学术内容 | 论文库 (Paper) | arXiv、PDF 等学术论文 |
| 网络文章 | 文章库 (Article) | 微信公众号、知乎等网络文章 |
| 个人笔记 | 笔记库 (Note) | 个人对话记录、学习笔记 |

**关联关系**：
- 笔记 (Note) ↔ 论文 (Paper)：多对多
- 文章 (Article) ↔ 论文 (Paper)：多对多
- 笔记 (Note) ↔ 笔记库内独立存在，可关联论文
- 文章 (Article) ↔ 文章库内独立存在，可关联论文"""

content = content.replace(old_design, new_design)

# 2. 添加 Article 数据模型（在 note_tags 之后）
article_model = """

### 2.4 Article 表（网络文章）

| 字段 | 类型 | 说明 |
|------|------|------|
| id | Integer | 主键 |
| title | String(500) | 文章标题 |
| content | Text | 文章正文 |
| author | String(200) | 作者 |
| source | String(50) | 来源：wechat / zhihu |
| url | String | 原文链接 |
| file_path | String | 本地文件路径 |
| published_at | Date | 发布时间 |
| is_deleted | Boolean | 软删除 |
| created_at | DateTime | 创建时间 |
| updated_at | DateTime | 更新时间 |

### 2.5 article_papers 关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| article_id | Integer | 外键 → articles.id |
| paper_id | Integer | 外键 → papers.id |
| created_at | DateTime | 关联时间 |

### 2.6 article_tags 关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| article_id | Integer | 外键 → articles.id |
| tag_id | Integer | 外键 → tags.id |
| created_at | DateTime | 关联时间 |"""

old_tags_table = """### 2.3 note_tags 关联表

| 字段 | 类型 | 说明 |
|------|------|------|
| note_id | Integer | 外键 → notes.id |
| tag_id | Integer | 外键 → tags.id |
| created_at | DateTime | 关联时间 |"""

content = content.replace(old_tags_table, old_tags_table + article_model)

# 3. 添加文章库 API（在笔记 API 之后）
article_api = """

### 3.4 文章库 CRUD

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/articles | 文章列表（支持筛选/搜索） | ✅ 已完成 |
| POST | /api/articles | 创建文章 | ✅ 已完成 |
| GET | /api/articles/:id | 获取文章详情 | ✅ 已完成 |
| PUT | /api/articles/:id | 更新文章 | ✅ 已完成 |
| DELETE | /api/articles/:id | 删除文章（软删除） | ✅ 已完成 |

### 3.5 文章-论文关联管理

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| POST | /api/articles/:id/papers | 关联论文到文章 | ✅ 已完成 |
| DELETE | /api/articles/:id/papers/:paper_id | 取消文章关联的论文 | ✅ 已完成 |

### 3.6 文章标签管理

| 方法 | 路径 | 说明 | 状态 |
|------|------|------|------|
| GET | /api/articles/:id/tags | 获取文章的所有标签 | ✅ 已完成 |
| POST | /api/articles/:id/tags | 给文章添加标签 | ✅ 已完成 |
| DELETE | /api/articles/:id/tags/:tag_id | 移除文章的标签 | ✅ 已完成 |"""

old_article_pos = "| DELETE | /api/notes/:id/tags/:tag_id | 移除笔记的标签 | ✅ 已完成 |\n\n---"
new_article_pos = "| DELETE | /api/notes/:id/tags/:tag_id | 移除笔记的标签 | ✅ 已完成 |" + article_api + "\n\n---"

content = content.replace(old_article_pos, new_article_pos)

# 4. 添加前端文章库功能（在笔记库独立页面之后）
article_frontend = """

### 4.4 文章库独立页面

| 功能 | 说明 | 状态 |
|------|------|------|
| 侧边栏入口 | 「📰 文章库」入口，与「论文库」「笔记库」并列 | ✅ 已完成 |
| 文章列表页 | 按来源筛选（微信/知乎）、关键词搜索 | ✅ 已完成 |
| 文章详情页 | 查看文章内容、原文链接 | ✅ 已完成 |
| 关联论文管理 | 在文章详情页关联/取消关联论文 | ✅ 已完成 |
| 跳转论文详情 | 点击关联论文可跳转到论文详情页 | ✅ 已完成 |
| 删除文章 | 确认后软删除文章 | ✅ 已完成 |

### 4.5 入库策略

| 内容类型 | 导入位置 | 跳转页面 |
|---------|---------|---------|
| arXiv 论文 | 论文库 | 论文库 |
| PDF 文件 | 论文库 | 论文库 |
| 微信公众号文章 | 文章库 | 文章库 |
| 知乎专栏文章 | 文章库 | 文章库 |
| 对话笔记 | 笔记库 | 笔记库 |"""

old_note_page = "### 4.3 笔记库独立页面\n\n| 功能 | 说明 | 状态 |\n|------|------|------|\n| 侧边栏入口 | 「笔记库」入口，与「论文库」并列 | ✅ 已完成 |\n| 笔记列表页 | 搜索、筛选、排序、分页 | ✅ 已完成 |\n| 笔记详情页 | 查看/编辑/删除笔记 | ✅ 已完成 |\n| 关联论文管理 | 在笔记详情页关联/取消关联论文 | ✅ 已完成 |\n| 自由笔记创建 | 不关联任何论文的笔记 | ✅ 已完成 |\n\n---"
new_note_page = "### 4.3 笔记库独立页面\n\n| 功能 | 说明 | 状态 |\n|------|------|------|\n| 侧边栏入口 | 「笔记库」入口，与「论文库」「文章库」并列 | ✅ 已完成 |\n| 笔记列表页 | 搜索、筛选、排序、分页 | ✅ 已完成 |\n| 笔记详情页 | 查看/编辑/删除笔记 | ✅ 已完成 |\n| 关联论文管理 | 在笔记详情页关联/取消关联论文 | ✅ 已完成 |\n| 自由笔记创建 | 不关联任何论文的笔记 | ✅ 已完成 |\n\n" + article_frontend + "\n\n---"

content = content.replace(old_note_page, new_note_page)

# 5. 添加文章库 TODO（在笔记标签管理之后）
article_todo = """

### 6.3 文章库功能（P1）

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| 文章库列表页 | P1 | 按来源筛选、关键词搜索 | ✅ 已完成 |
| 文章详情页 | P1 | 查看内容、原文链接 | ✅ 已完成 |
| 文章关联论文 | P1 | 关联/取消关联论文 | ✅ 已完成 |
| 文章标签管理 | P2 | 和论文/笔记共用 Tag 系统 | 待开发 |

### 6.4 Markdown 渲染（P2）

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| 笔记内容 Markdown 渲染 | P2 | 将笔记内容渲染为 HTML | 待开发 |
| 文章内容 Markdown 渲染 | P2 | 将文章内容渲染为 HTML | 待开发 |
| 代码块高亮 | P2 | 使用 highlight.js | 待开发 |

### 6.5 对话笔记正式迁移（P2）

| 功能 | 优先级 | 说明 | 状态 |
|------|--------|------|------|
| 后台手动触发迁移 | P2 | 一键将所有对话笔记 Paper 转为 Note | 待开发 |
| 迁移进度展示 | P2 | 显示迁移了多少篇 | 待开发 |
| 迁移回滚 | P2 | 如有问题可回滚 | 待开发 |"""

old_todo = "### 6.3 笔记搜索（P2）\n\n| 功能 | 优先级 | 说明 |\n|------|--------|------|\n| 笔记关键词搜索 | P2 | 标题 + 内容搜索 |\n| 搜索高亮 | P2 | 匹配词高亮显示 |\n\n### 6.4 Markdown 渲染（P2）\n\n| 功能 | 优先级 | 说明 |\n|------|--------|------|\n| 笔记内容 Markdown 渲染 | P2 | 将笔记内容渲染为 HTML |\n| 代码块高亮 | P2 | 使用 highlight.js |\n\n### 6.5 对话笔记正式迁移（P2）\n\n| 功能 | 优先级 | 说明 |\n|------|--------|------|\n| 后台手动触发迁移 | P2 | 一键将所有对话笔记 Paper 转为 Note |\n| 迁移进度展示 | P2 | 显示迁移了多少篇 |\n| 迁移回滚 | P2 | 如有问题可回滚 |"""

content = content.replace(old_todo, article_todo)

# 6. 更新数据库变更记录
old_db_change = """| 2026-05-01 | 新增 `notes` 表 | 笔记主表 |
| 2026-05-01 | 新增 `note_papers` 表 | 笔记-论文多对多关联 |
| 2026-05-01 | 新增 `note_tags` 表 | 笔记-标签多对多关联 |
| 2026-05-01 | `papers` 表新增 `extra` 列 | 兼容迁移 |"""

new_db_change = """| 2026-05-01 | 新增 `notes` 表 | 笔记主表 |
| 2026-05-01 | 新增 `note_papers` 表 | 笔记-论文多对多关联 |
| 2026-05-01 | 新增 `note_tags` 表 | 笔记-标签多对多关联 |
| 2026-05-01 | `papers` 表新增 `extra` 列 | 兼容迁移 |
| 2026-05-01 | 新增 `articles` 表 | 文章主表（微信/知乎） |
| 2026-05-01 | 新增 `article_papers` 表 | 文章-论文多对多关联 |
| 2026-05-01 | 新增 `article_tags` 表 | 文章-标签多对多关联 |"""

content = content.replace(old_db_change, new_db_change)

# 7. 更新文件清单
old_file_list = """| backend/models/paper.py | 更新：Note 模型 + 新增 `url`/`file_path`/`published_at` 字段 |
| backend/api/notes.py | 新增：笔记 CRUD API |
| backend/api/ingest.py | 重构：非学术内容入库进笔记库 |
| backend/services/migrate_notes.py | 新增：对话笔记迁移脚本 |
| migrate_notes_add_fields.py | 新增：数据库字段迁移脚本 |
| frontend/index.html | 更新：论文详情页笔记 Tab + 笔记库页面 + 笔记跳转功能 |
| frontend/src/modules/ingestModule.js | 更新：微信公众号导入跳转到笔记库 |
| frontend/src/modules/fileUploadModule.js | 更新：HTML/PDF 分别跳转到不同库 |
| frontend/src/api/index.js | 更新：IngestAPI 兼容新旧方法名 |"""

new_file_list = """| backend/models/paper.py | 更新：Note 模型 + Article 模型 + 关联表 |
| backend/api/notes.py | 笔记 CRUD API |
| backend/api/articles.py | 新增：文章库 CRUD API |
| backend/api/ingest.py | 重构：微信/知乎→文章库，对话笔记→笔记库 |
| backend/services/migrate_notes.py | 对话笔记迁移脚本 |
| backend/services/note_deduplicator.py | 笔记去重工具 |
| backend/services/article_deduplicator.py | 文章去重工具 |
| migrate_notes_add_fields.py | 笔记表字段迁移脚本 |
| migrate_create_articles.py | 新增：创建文章库相关表 |
| dedup_notes.py | 新增：命令行笔记去重工具 |
| frontend/index.html | 更新：论文库 + 文章库 + 笔记库页面 |
| frontend/src/modules/ingestModule.js | 更新：微信导入跳转到文章库 |
| frontend/src/modules/fileUploadModule.js | 更新：HTML→文章库，PDF→论文库 |
| frontend/src/api/articles.js | 新增：文章库 API 封装 |
| frontend/src/api/index.js | 更新：IngestAPI 兼容新旧方法名 |"""

content = content.replace(old_file_list, new_file_list)

# 8. 更新时间戳
content = content.replace("*最后更新: 2026-05-01*", "*最后更新: 2026-05-01 (新增文章库)*")

with open('/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/docs/笔记系统设计方案.md', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ 文档已更新完成！")
