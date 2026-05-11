# 项目目录结构与模块规约

## 目标
明确前后端目录结构职责，规范模块划分，保证项目可扩展与可维护。

## 项目目录总览
```
PaperHub/
├── backend/
│   ├── api/
│   ├── services/
│   ├── models/
│   ├── app.py
│   └── config.py
├── frontend/
│   ├── pages/
│   └── modules/
└── SPECS/
```

## 后端规约（Flask 框架）

### 1. backend/api/
- 职责：仅存放 API 路由层
- 规则：
  - 每个业务模块对应一个文件，snake_case 命名
  - 只做请求参数校验、调用 services、返回统一格式响应
  - 禁止直接写业务逻辑
  - 所有 Blueprint 在此注册
- 示例：papers.py, notes.py, ingest.py, backup.py

### 2. backend/services/
- 职责：存放核心业务逻辑层
- 规则：
  - 每个业务服务对应一个模块或类文件，snake_case 命名
  - 所有复杂业务逻辑、外部调用、数据处理在此实现
  - 不直接处理 HTTP 请求对象
  - 可调用 models 进行数据库操作
- 示例：pdf_processor.py, web_parser.py, llm_client.py

### 3. backend/models/
- 职责：存放 ORM 数据模型层
- 规则：
  - 使用 SQLAlchemy 定义数据表映射
  - 仅做数据模型定义、基础查询封装
  - 禁止包含复杂业务逻辑
  - 类名采用帕斯卡命名
- 示例：paper.py

## 前端规约（单页应用 CDN 版本）

### 1. frontend/pages/
- 职责：存放页面级代码
- 规则：
  - 按功能页划分，snake_case 命名
  - 每个页面对应独立的 HTML 片段或初始化逻辑
  - 负责页面渲染、事件绑定
  - 不存放复杂通用工具函数

### 2. frontend/modules/
- 职责：存放可复用模块与工具
- 规则：
  - 业务模块文件 snake_case 命名，如 file_upload_module.js
  - 工具函数文件 snake_case 命名，如 sort_utils.js, filter_utils.js
  - 工具函数内部采用小驼峰命名（仅此处允许）
  - 抽取可复用逻辑，避免代码重复
- 示例：filterUtils.js, sortUtils.js, fileUploadModule.js

### 3. 前端静态资源
- frontend/src/css/：样式文件，snake_case 命名
- frontend/src/js/：页面脚本文件，snake_case 命名
- index.html：应用入口

## 约束
- 新增模块必须严格放入对应目录
- 禁止跨层反向依赖（如 models 不能调用 services）
- API 层不能直接写业务逻辑，必须下沉到 services

## 验收标准
- 目录结构完全符合 backend/api/services/models + frontend/pages/modules 规范
- 无跨层反向依赖
- 各层职责清晰、无代码混杂
