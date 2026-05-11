# 命名规范规约

## 目标
统一全项目命名体系，消除命名歧义，保证代码一致性与可维护性。

## 规则

### 1. 后端文件命名
- 规则：全部 snake_case
- 示例：papers.py, wechat_subscription.py, note_deduplicator.py
- 禁止：驼峰、帕斯卡命名

### 2. 后端接口路由命名
- 规则：全部 snake_case
- 示例：/api/get_papers, /api/add_note, /api/wechat_import
- 禁止：驼峰、短横线命名

### 3. 数据库字段命名
- 规则：全部 snake_case
- 示例：published_at, category_l1, file_path, note_images
- 禁止：驼峰、帕斯卡命名

### 4. Python 变量与函数命名
- 规则：全部 snake_case
- 示例：def get_paper_list(), paper_title, import_status
- 禁止：驼峰、帕斯卡命名（类名除外）

### 5. Python 类命名
- 规则：帕斯卡命名（仅用于类名）
- 示例：Paper, NoteDeduplicator, WebParser
- 例外：仅类名允许帕斯卡，其他所有命名遵循 snake_case

### 6. 前端文件命名
- 规则：全部 snake_case
- 示例：file_upload_module.js, sort_utils.js
- 禁止：驼峰、帕斯卡命名

### 7. 前端工具函数命名
- 规则：小驼峰 camelCase
- 示例：getPaperList(), formatDate(), filterByStatus()
- 例外：仅工具函数允许小驼峰，其他遵循 snake_case

### 8. 前端变量命名
- 规则：全部 snake_case
- 示例：selected_paper_id, note_content_list
- 禁止：帕斯卡命名

## 约束
- 任何新增代码必须严格遵守此规范
- 代码评审时需先检查命名规范
- 禁止引入新的非合规命名

## 验收标准
- grep 代码库无不符合 snake_case 的文件、接口、数据库字段命名
- 前端仅工具函数使用小驼峰，其余全部 snake_case
