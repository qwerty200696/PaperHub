# PaperHub - 实施 Checklist

---

## 🎉 **Phase 0-5 全部完成！2026.5.2 里程碑**

---

## Phase 0: 代码质量优化与模块化重构 ✅
**目标**: 清理技术债务，建立可持续开发的架构

- [x] **0.1 前端模块化拆分**
  - [x] CSS 独立分离 `src/css/style.css`
  - [x] API 层封装 `src/api/index.js`
  - [x] 工具函数独立 `src/utils/index.js`
  - [x] 筛选模块 `src/modules/filterModule.js`
  - [x] 论文操作模块 `src/modules/paperModule.js`
  - [x] 标签管理模块 `src/modules/tagModule.js`
  - [x] 排序逻辑模块 `src/modules/sortModule.js`
  - [x] 入库功能模块 `src/modules/ingestModule.js`
  - [x] 文件上传模块 `src/modules/fileUploadModule.js`
  - [x] 成果：1200 行 → 961 行 **-279 行**

- [x] **0.2 后端技术债务修复**
  - [x] 统一 Session 管理 `config.py scoped_session`
  - [x] 全局异常拦截 `@app.errorhandler(Exception)`
  - [x] 日志系统 `logging.basicConfig`

- [x] **0.3 用户体验优化**
  - [x] 入库成功后自动刷新
  - [x] 删除后保持当前筛选
  - [x] 标签点击区域优化
  - [x] 详情页返回恢复筛选

---

## Phase 1: 基础骨架 (MVP) ✅
**目标**: 可运行的基础版本，支持PDF入库、分类、基础展示

- [x] **1.1 项目目录初始化**
  - [x] 创建 `backend/` 目录结构
  - [x] 创建 `frontend/` 目录结构
  - [x] 创建 `data/` 子目录 (papers, db, vectors, backups)
  - [x] 创建 `docs/` 目录
  - [x] 创建 `scripts/` 目录

- [x] **1.2 数据库设计 + SQLAlchemy 模型**
  - [x] 编写 `docs/SCHEMA.md`
  - [x] 创建 `backend/models/` 基础结构
  - [x] 实现 `Paper` 模型
  - [x] 实现 `Tag` 模型
  - [x] 实现 `PaperTag` 关联模型
  - [x] 实现 `Note` 模型
  - [x] 实现 `PaperVersion` 模型
  - [x] 编写数据库初始化脚本

- [x] **1.3 Flask 后端基础框架**
  - [x] 创建 `backend/requirements.txt`
  - [x] 创建 `backend/config.py`
  - [x] 创建 `backend/app.py` 主入口
  - [x] 设置 CORS 支持
  - [x] 配置 SQLAlchemy 数据库连接

- [x] **1.4 arXiv 抓取功能**
  - [x] 创建 `backend/services/arxiv_fetcher.py`
  - [x] 实现 arXiv ID / 链接解析
  - [x] 实现元数据抓取 (标题/作者/摘要/时间)
  - [x] 实现 PDF 下载功能
  - [x] 创建 arXiv 入库 API `POST /api/ingest/arxiv`

- [x] **1.5 论文基础 API**
  - [x] 创建 `backend/api/papers.py`
  - [x] `GET /api/papers` - 论文列表 (分页)
  - [x] `GET /api/papers/:id` - 论文详情
  - [x] `PUT /api/papers/:id` - 更新论文 (分类/状态)
  - [x] `DELETE /api/papers/:id` - 删除论文
  - [x] `GET /api/papers/:id/download` - 下载PDF

- [x] **1.6 基础前端 (Vue 3)**
  - [x] 初始化 Vue 3 + Vite 项目 (CDN 版本)
  - [x] 安装 Element Plus 组件库
  - [x] 配置路由 (内置简单路由)
  - [x] 创建基础布局组件
  - [x] Library.vue - 论文列表页
  - [x] PaperDetail.vue - 论文详情页
  - [x] Ingest.vue - 入库页 (仅arXiv)

- [x] **1.7 PDF 内嵌预览**
  - [x] 使用浏览器内置 PDF 预览
  - [x] 在 PaperDetail 中展示 PDF
  - [x] 浏览器原生支持翻页/缩放

- [x] **1.8 MVP 测试**
  - [x] 测试 arXiv 入库流程 - 成功入库 2604.08224
  - [x] 测试论文列表展示
  - [x] 测试 PDF 预览
  - [x] 测试论文编辑/删除

---

## Phase 2: 多源入库 & 标签系统 ✅ 全部完成

- [x] **2.1 微信公众号文章抓取**
  - [x] 创建 `backend/services/wechat_parser.py`
  - [x] 实现公众号链接解析 (URL + 本地HTML两种方式)
  - [x] 实现正文内容提取 + 图片本地化处理
  - [x] 实现图片防盗链完整解决方案 - 无"未经允许不可引用"
  - [x] 创建公众号入库 API `POST /api/ingest/wechat`
  - [x] ✨ 方案2升级：完整HTML保留所有JS，iframe自动渲染时间/位置
  - [x] 元数据提取：发布时间（精确到分钟）+ IP地理位置

- [x] **2.2 批量PDF导入**
  - [x] 实现文件上传接口，支持HTML/PDF
  - [x] 创建 `backend/services/pdf_processor.py`
  - [x] 前端批量上传组件，支持拖拽
  - [x] HTML文件自动识别为微信文章

- [x] **2.3 去重机制**
  - [x] 创建 `backend/services/deduplicator.py`
  - [x] 基于URL去重（微信/arXiv）
  - [x] 基于标题哈希去重
  - [x] 入库前重复检测与跳过

- [x] **2.4 标签系统**
  - [x] 实现标签关联 API
  - [x] 前端论文库直接打标签，无需进详情页
  - [x] 二级分类预设数据
  - [x] 侧边栏标签筛选，高频标签优先

- [x] **2.5 论文删除功能**
  - [x] 实现 `DELETE /api/papers/:id` API
  - [x] 数据库 + 文件系统联动清理
  - [x] 前端确认对话框
  - [x] 列表页 + 详情页双入口删除

- [x] **2.6 来源标识与元数据展示**
  - [x] 论文库优雅区分：微信URL / 微信本地 / arXiv
  - [x] 微信文章显示发布时间标签
  - [x] arXiv论文显示论文ID标签

---

## Phase 3: 对话笔记 & 多维筛选 ✅ 全部完成

- [x] **3.1 对话笔记导入功能**
  - [x] 新增"对话笔记"入库标签页
  - [x] 支持 Markdown 格式正文
  - [x] Markdown 转 HTML 渲染，精美排版
  - [x] 同时保存 .md 和 .html 两个文件
  - [x] HTML 预览模式（非PDF）
  - [x] 来源单选按钮组：豆包 / Kimi / 千问 / DeepSeek / Claude / ChatGPT
  - [x] 支持自定义新增来源
  - [x] 标题自动提取（正文第一行，去掉markdown）
  - [x] 日期默认当前时间，可手动调整
  - [x] 笔记删除时同时清理 .md 和 .html 两个文件

- [x] **3.2 多维度组合筛选系统**
  - [x] 分门别类：系统内置标签 vs 用户自定义标签
  - [x] 📊 **来源筛选** - arXiv / 微信URL / 对话笔记
  - [x] 📅 **日期筛选** - 三档粒度切换
    - [x] **年** - [起始] 年 ~ [结束] 年，纯文本输入
    - [x] **月** - [年]年[月]月 ~ [年]年[月]月，纯文本输入
    - [x] **日** - 日期范围选择器
  - [x] 🏷️ **用户标签筛选**
  - [x] 一键清除全部筛选
  - [x] 多条件组合筛选
  - [x] 选中计数实时显示

- [x] **3.3 UI 交互优化**
  - [x] 侧边栏支持拖拽调整宽度 (180px - 450px)
  - [x] 日期输入前验证 + 友好提示
  - [x] 互斥筛选状态自动维护
  - [x] "批量PDF上传" 改名为 "批量PDF/HTML上传"

---

## Phase 4: 知乎导入 & 视觉化 & 排序 ✅ 全部完成

- [x] **4.1 知乎专栏/文章导入**
  - [x] 新增"知乎"入库标签页
  - [x] 双模式支持：URL自动解析 + 手动内容粘贴
  - [x] Cookie 身份认证，突破知乎 403 反爬限制
  - [x] 自动保存 HTML + Markdown 双文件
  - [x] Cookie 自动记忆，上次成功的自动填充
  - [x] Cookie 获取工具脚本 `tools/zhihu_cookie_get.py`

- [x] **4.2 标星与阅读状态视觉化升级**
  - [x] ★ 星星直接显示在标题前，一目了然
  - [x] 📚 侧边栏状态统计 + 快速筛选按钮
  - [x] 🎨 四种状态专属视觉区分
    - [x] 待读 - 绿色左边界 + 「新」红色徽章
    - [x] 在读 - 蓝色左边界
    - [x] 精读 - 橙色左边界
    - [x] 标星 - 紫色左边界
  - [x] 已读文章降低对比度，视觉降噪
  - [x] 修复"全部"状态统计始终为 0 的 bug
  - [x] 修复标星图标不显示的 bug（Element Plus 组件 → Unicode 字符）

- [x] **4.3 首页五合一排序系统**
  - [x] 🕒 按添加时间 - 默认，新入库排最前
  - [x] ⭐ 收藏优先 - 标星置顶，同优先级按状态
  - [x] 📚 阅读状态 - 待读 → 在读 → 精读 → 已读
  - [x] 📅 发布日期 - 文章本身发布时间倒序
  - [x] 🔤 标题排序 - 中文拼音正确排序
  - [x] localStorage 记住用户排序偏好
  - [x] 💣 踩坑修复：`||` 运算符导致 pending 权重错误（史诗级坑）

---

## Phase 5: 三大模块统一架构 ✅ **2026.5.2 全部完成**

### ✅ **5.1 文章库独立化**

- [x] **5.1.1 历史数据迁移**
  - [x] 分析论文库中遗留的微信/知乎文章分布
  - [x] 编写迁移脚本 `migrate_wechat_zhihu_to_articles.py`
  - [x] 修复表结构不匹配问题
  - [x] 修复 ID 冲突问题（8,9,13,14 → 15,16,17,18）
  - [x] 成功迁移 4 篇：2 微信 + 2 知乎
  - [x] 验证数据完整性

- [x] **5.1.2 404 路由修复**
  - [x] 知乎静态文件专门路由：`/static/zhihu/<filename>`
  - [x] 前端 `getArticlePreviewUrl` 函数：动态构造预览路径
  - [x] 支持微信/知乎两种路径格式自动识别
  - [x] 验证迁移后所有文章可正常预览

- [x] **5.1.3 文章库体验优化**
  - [x] 作者格式化：去掉 JSON 数组括号 `["AI玩家日志"]` → `AI玩家日志`
  - [x] 编写 `formatAuthor` 工具函数
  - [x] 列表页 / 详情页所有作者展示统一格式化

### ✅ **5.2 笔记库重大升级**

- [x] **5.2.1 Markdown 完整渲染**
  - [x] 添加 marked.js CDN 引入
  - [x] 编写 `renderMarkdown` 渲染函数（含异常处理）
  - [x] `.note-markdown` 专属 CSS 类
  - [x] 支持所有 Markdown 元素：
    - [x] H1-H6 标题层级 + 下划线
    - [x] 行内代码（浅灰底 + 橙色文字）
    - [x] 代码块深色主题 + 语法高亮
    - [x] 引用块蓝边 + 浅蓝背景
    - [x] 表格完整边框 + 表头灰底
    - [x] 列表缩进 + 间距
    - [x] 链接蓝色下划线悬停效果

- [x] **5.2.2 智能同步标签功能**
  - [x] 笔记详情页新增「🔄 同步关联标签」按钮
  - [x] 收集关联论文的所有标签
  - [x] 收集关联文章的所有标签
  - [x] 自动去重（排除笔记已有标签）
  - [x] 批量添加 + 成功提示
  - [x] **关键修复**：`Note.to_dict()` 递归序列化关联 papers/articles 时包含 tags

- [x] **5.2.3 笔记详情页布局优化**
  - [x] 【优先级最高】笔记正文 Markdown 渲染放在最前面
  - [x] 标签管理区移到正文下方（含同步按钮）
  - [x] 关联论文列表
  - [x] 关联文章列表
  - [x] 调整边距和边框，优化视觉层次

### ✅ **5.3 标签系统三大模块统一化**

- [x] **5.3.1 文章库标签独立筛选**
  - [x] 创建 `articleAllTags` / `articleSelectedTagIds` 独立状态变量
  - [x] 前端实时统计每个标签的 `article_count`
  - [x] 只显示有文章的标签
  - [x] 侧边栏「阅读状态」下方新增「文章标签」筛选区

- [x] **5.3.2 笔记库标签独立筛选**
  - [x] 创建 `noteAllTags` / `noteSelectedTagIds` 独立状态变量
  - [x] 前端实时统计每个标签的 `note_count`
  - [x] 只显示有笔记的标签
  - [x] 侧边栏「笔记状态」下方新增「笔记标签」筛选区

- [x] **5.3.3 三模块 100% 一致性**
  - [x] 布局完全一致：状态筛选在上，标签筛选在下
  - [x] 交互完全一致：点击切换标签选中状态
  - [x] 排序算法完全复用：标星 → 状态 → 时间
  - [x] CSS 类完全复用：三模块共用一套状态配色
  - [x] **关键修复**：进入详情页重新拉取完整数据（包含 tags）

### ✅ **5.4 AI 解读功能（2026.5.5）**

- [x] **5.4.1 论文 AI 解读**
  - [x] 后端 `backend/api/ai.py` - AI 解读 API
  - [x] 后端 `backend/services/llm_client.py` - 多提供商支持
  - [x] 前端 AI 解读按钮 + 配置弹窗
  - [x] 笔记自动生成，标题格式 `AI解读：论文标题`
  - [x] 笔记来源标记为 `AI解读`
  - [x] 自动关联到当前论文
  - [x] 即时显示在论文详情页笔记列表

- [x] **5.4.2 多提供商支持**
  - [x] 豆包、OpenAI、通义千问、Anthropic、TEG（自定义）
  - [x] API Key 本地存储持久化
  - [x] 支持 temperature 配置

- [x] **5.4.3 笔记去重算法优化**
  - [x] 改用词级别 Jaccard 相似度（权重 60%）
  - [x] 字符级相似度 + 编辑距离辅助（各 20%）
  - [x] 修复不同论文 AI 解读被误判为重复的问题

### ✅ **5.5 论文元数据编辑**

- [x] **5.5.1 编辑功能**
  - [x] 论文详情页右上角「编辑元数据」按钮
  - [x] 支持编辑：标题、arXiv ID、作者、摘要、分类
  - [x] 保存后即时刷新显示

- [x] **5.5.2 arXiv ID 标签显示**
  - [x] 手动上传的 PDF 支持添加 arXiv ID
  - [x] 列表页和详情页显示 arXiv 标签

### ✅ **5.6 排序偏好持久化**

- [x] **5.6.1 三库独立记忆**
  - [x] 论文库 `sortBy` - localStorage 持久化
  - [x] 文章库 `articleSortBy` - localStorage 持久化
  - [x] 笔记库 `noteSortBy` - localStorage 持久化
  - [x] 初始化时自动加载上次选择

---

## 完成统计（2026-05-05）

| Phase | 完成项 / 总项 | 进度 | 说明 |
|-------|--------------|------|------|
| Phase 0 | 3 / 3 | **100%** | 代码重构/优化/模块化 |
| Phase 1 | 8 / 8 | **100%** | MVP 完成 |
| Phase 2 | 6 / 6 | **100%** | 多源入库 & 标签系统 |
| Phase 3 | 3 / 3 | **100%** | 对话笔记 & 多维筛选 |
| Phase 4 | 3 / 3 | **100%** | 知乎导入 & 视觉化 & 排序 |
| Phase 5 | 3 / 3 | **100%** | 三大模块统一架构 |
| **总计** | **26 / 26** | **100%** | **基础功能 + 架构统一 全部完成！** |

---

## Phase 6: 检索与知识库 ✅ **2026.5.8 完成**

### ✅ 6.1 arXiv 关键词检索功能

- [x] **后端服务扩展** (`backend/services/arxiv_fetcher.py`)
  - [x] `search_arxiv_papers()` - 核心搜索函数
  - [x] `get_arxiv_categories()` - 返回70+个arXiv分类
  - [x] 支持多关键词组合搜索
  - [x] 支持分类筛选、时间范围过滤、排序

- [x] **API端点** (`backend/api/papers.py`)
  - [x] `GET /api/papers/search` - 搜索arXiv论文
  - [x] `GET /api/papers/search/categories` - 获取分类列表
  - [x] `POST /api/papers/search/import` - 批量导入搜索结果

- [x] **前端界面**
  - [x] arXiv入库tab下新增"方法二：关键词搜索"
  - [x] 论文库页面右上角"Arxiv论文检索"快捷按钮
  - [x] 支持单选/全选、批量导入（元数据/含PDF）

### ✅ 6.2 微信公众号订阅功能

- [x] **后端模型** (`backend/models/paper.py`)
  - [x] `WechatSubscription` 模型（公众号名称、biz号、最后检查时间）

- [x] **API端点** (`backend/api/wechat_subscription.py`)
  - [x] `GET /api/wechat/subscriptions` - 获取订阅列表
  - [x] `POST /api/wechat/subscriptions` - 添加订阅
  - [x] `DELETE /api/wechat/subscriptions/{id}` - 删除订阅
  - [x] `POST /api/wechat/subscriptions/check` - 检查新文章
  - [x] `GET /api/wechat/search_account` - 搜索公众号

- [x] **前端功能**
  - [x] 单选形式订阅公众号
  - [x] 公众号搜索（使用第三方API）
  - [x] 检查新文章（显示最新5篇，支持查看更多）
  - [x] 标记文章是否已导入
  - [x] 批量导入选中文章
  - [x] 第三方API密钥配置

### ✅ 6.3 文章详情页笔记功能

- [x] **笔记入口**
  - [x] 文章详情页操作栏添加「📝 写笔记」按钮
  - [x] 关联笔记模块仅在有笔记时显示

- [x] **双向关联**
  - [x] 新增笔记自动关联当前文章
  - [x] 文章详情页显示关联笔记
  - [x] 笔记详情页显示关联文章
  - [x] 删除笔记后自动刷新文章页面

### ✅ 6.4 文章元数据编辑

- [x] **编辑功能**
  - [x] 文章详情页「编辑元数据」按钮
  - [x] 支持编辑：标题、作者、原文链接、发布日期、摘要

- [x] **删除确认**
  - [x] 所有删除按钮添加二次弹窗确认

### ✅ 6.5 微信正文提取优化

- [x] **样式清理**
  - [x] 清理微信冗余属性（class、style、data-*）
  - [x] 保留有用样式（text-align、font-weight、color、background-color）
  - [x] 清理底部栏（赞、分享、推荐、写留言等）

- [x] **内容保留**
  - [x] 保留图片、代码块、表格、列表
  - [x] 代码块正确换行显示
  - [x] 表格响应式处理（横向滚动）
  - [x] 橙色装饰方块保留并正确对齐

### ✅ 6.6 SQLite 全文检索（已完成）
**目标**: 实现基于关键词的搜索，当论文超过 100 篇时筛选不够用
**详细设计文档**: `docs/SQLite_FTS5_全文检索规划.md`

- [x] **6.6.1 配置 SQLite FTS5**
  - [x] 创建 FTS5 虚拟表迁移脚本 `migrations/006_add_fts_tables.py`
  - [x] 创建触发器实现增量同步（insert/update/delete）
  - [x] 配置三库索引字段（论文/文章/笔记）

- [x] **6.6.2 后端搜索 API**
  - [x] `GET /api/search?q=关键词` - 搜索接口（支持跨模块搜索）
  - [x] `GET /api/search/suggest` - 搜索建议接口
  - [x] 支持高亮匹配结果
  - [x] 支持分页展示

- [x] **6.6.3 前端搜索面板**
  - [x] 顶部搜索栏（和浏览器地址栏对齐）
  - [x] 实时搜索（输入时即时响应）
  - [x] 搜索结果展示（高亮关键词）
  - [x] 搜索历史记录（localStorage）

### 📋 6.7 UX 优化（快速完成）

- [ ] **6.7.1 筛选后页码自动重置**
  - [ ] 筛选/排序时重置到第 1 页
- [ ] **6.7.2 批量操作**
  - [ ] 批量删除
  - [ ] 批量打标签
  - [ ] 批量改状态

### 📋 6.8 导出与同步（低优先级但实用）

- [ ] **6.8.1 单篇论文导出**
  - [ ] 导出 PDF（已有下载功能）
  - [ ] 导出 Markdown（对话笔记已有）
  - [ ] 导出元数据 JSON

- [ ] **6.8.2 批量导出**
  - [ ] 支持按筛选导出（当前搜索结果/标签）
  - [ ] 生成论文库索引
  - [ ] 打包成 ZIP 文件

---

## Phase 7: 科研辅助工具（长期）

### 📋 7.1 arXiv 版本更新检测

- [ ] 检测 arXiv 论文版本更新
- [ ] 新旧版本保存
- [ ] 版本差异展示（可选）

### 📋 7.2 数据备份/恢复

- [ ] 创建 `scripts/backup.py`
- [ ] 创建 `scripts/restore.py`
- [ ] 数据库 + PDF 打包备份
- [ ] 前端备份管理页面

### 📋 7.3 向量语义检索

- [ ] ChromaDB 集成
- [ ] 文本向量化
- [ ] 语义相似度搜索

---

## 🎯 下一步行动计划（建议优先级）

### 🔥 **高优先级：Phase 6.1 SQLite 全文检索**
- **预计工作量**：1 天
- **价值**：当内容超过 100 篇，筛选 + 排序就不够用了，搜索是刚需
- **技术风险**：低，SQLite FTS5 内置支持

---

> 💡 **当前项目状态：S 级 - 架构清晰，文档完善，技术债务已清理，可以继续快速迭代！**

*文档最后更新：2026-05-05*
