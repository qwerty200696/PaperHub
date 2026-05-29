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

#---

## Phase 7: 搜索体验全面升级 ✅ **2026.5.8 全部完成**

### ✅ 7.1 搜索框 V1.3 体验升级

- [x] **FTS5 rank加权融合排序**
  - [x] 后端 search_service.py 优化，不再简单固定权重，1/(fts_rank+1) * 模块权重
  - [x] 三模块搜索显式获取 rank 字段，结果相关性大幅提升

- [x] **前端交互优化**
  - [x] 300ms防抖机制，handleSearchInput，网络请求量减少70%+
  - [x] AbortController 请求取消，新输入自动取消上一个未完成的建议请求，解决响应乱序问题
  - [x] 新增 searchLoading 状态变量，搜索过程中显示旋转的 spinner

- [x] **键盘导航**
  - [x] 选中项高亮状态变量 selectedSuggestionIndex
  - [x] 处理 keydown 事件：上箭头 / 下箭头移动选中高亮
  - [x] Enter 键直接选中当前高亮项执行搜索
  - [x] ESC 键一键关闭下拉面板
  - [x] 鼠标 hover 自动同步高亮当前项

- [x] **业界标准快捷键**
  - [x] 全局 Ctrl+K / Cmd+K 快捷键监听，不管页面哪里按下，搜索框立刻聚焦
  - [x] 防止浏览器默认行为，不冲突

- [x] **LRU本地缓存**
  - [x] Map结构最多缓存20条搜索结果
  - [x] 命中时自动把键移到末尾标记最近使用，满20条自动删除最久未使用的
  - [x] 大小写无关缓存，搜Paper和paper命中同一条
  - [x] 完全跳过网络请求，第二次搜同样关键词结果秒返回

- [x] **大动态加载状态**
  - [x] 搜索结果弹窗添加醒目的64px超大旋转⏳图标
  - [x] 「正在搜索中...」蓝色大字文案，一按回车立刻覆盖旧结果
  - [x] 仅非缓存命中的真实网络搜索进入searchLoading，缓存命中直接秒返回

- [x] **点击外部关闭下拉面板**
  - [x] 捕获阶段监听器，addEventListener第3个参数传true
  - [x] 搜索容器加@click.stop阻止内部事件冒泡
  - [x] onMounted注册，onUnmounted移除，成对操作无内存泄漏

- [x] **样式完善**
  - [x] CSS搜索结果高亮：黄色背景 + 粗体 + 圆角
  - [x] @keyframes spin 流畅旋转动画效果
  - [x] 下拉选中项淡蓝色高亮（#ecf5ff），比hover灰色更醒目

### ✅ 7.2 日志系统优化

- [x] **扫描请求自动过滤**
  - [x] ScanFilter继承自logging.Filter
  - [x] _scan_patterns列表覆盖常见扫描探测路径特征
  - [x] 挂载到werkzeug日志器，访问日志清爽
  - [x] 全局异常处理器里新增判断，NotFound且路径属于扫描特征直接返回404，不打ERROR堆栈
  - [x] HTTPException统一返回原始状态码，不再全当500错误

---

## Phase 8: 笔记图片粘贴上传 + 清理重构 ✅ **2026.5.9 全部完成**

### ✅ 8.1 笔记图片粘贴上传功能

- [x] **后端API**
  - [x] config.py新增NOTE_IMAGES_DIR目录配置
  - [x] note_images.py全新创建图片上传API
  - [x] 静态资源路由注册，/static/note_images/直接访问

- [x] **前端交互**
  - [x] setupNoteEditorPasteHandler()绑定文本域paste事件
  - [x] 粘贴事件获取clipboardData.items，识别图片类型
  - [x] FormData包装文件，axios POST上传到/api/note-images/upload
  - [x] 上传成功后自动在光标位置生成 ![图片](/static/note_images/xxx.png) Markdown
  - [x] 支持新建笔记和编辑笔记两种场景

### ✅ 8.2 新建笔记双重弹窗重叠修复

- [x] 全局搜索noteEditorVisible绑定的弹窗
  - [x] 删除第1处：笔记库列表页内约734行重复弹窗
  - [x] 删除第2处：笔记详情页内约832行重复弹窗
  - [x] 全局仅保留最后那个独立在全局区域的笔记编辑器弹窗

### ✅ 8.3 旧模块化代码清理

- [x] **删除废弃文件**
  - [x] 清理所有历史遗留未被import的16个模块文件，共删除-3029行冗余代码
  - [x] noteModule.js / paperModule.js / articleModule.js / searchModule.js / filterModule.js 等全部移除
  - [x] 只保留4个真正被动态 import 使用的工具模块：sortUtils / filterUtils / ingestModule / fileUploadModule

- [x] **清理window.开头兼容代码**
  - [x] 全局搜索所有 if (window.xxx) 代理判断代码，全部删除
  - [x] 清理130行冗余兼容代码
  - [x] downloadPaper直接用原生window.open，完全不需要旧模块代理
  - [x] getCurrentDateTime本地原生实现，完全独立运行

---

## Phase 9: 三库硬删 + 微信时间精确修复 ✅ **2026.5.10 全部完成**

### ✅ 9.1 三库删除策略统一硬删除

- [x] **文章库硬删改造**
  - [x] 移除查询时is_deleted==False软删除过滤
  - [x] 不再标记is_deleted=True，直接session.delete(article)从数据库硬删
  - [x] 安全校验file_path必须在data/papers/wechat目录下，防止路径遍历
  - [x] 先删除.html文件，再删除同目录下对应文件名的_files图片文件夹
  - [x] 有异常捕获，清理失败不影响主流程

- [x] **笔记库硬删改造**
  - [x] 移除查询时is_deleted==False软删除过滤
  - [x] 直接session.delete(note)从数据库硬删
  - [x] 正则解析笔记Markdown内容，提取所有 /static/note_images/ 路径的图片
  - [x] 安全校验确保文件在data/papers/note_images目录下
  - [x] 逐个删除对应本地图片文件

### ✅ 9.2 微信公众号发布时间精确修复

- [x] **新增轻量辅助函数**
  - [x] _extract_published_at_only(url)，轻量爬取原始微信页面
  - [x] 不下载图片，不保存任何文件，仅做一件事：提取准确发布时间
  - [x] 复用和旧函数完全相同的时间提取逻辑，保证准确性

- [x] **批量修正脚本**
  - [x] scripts/maintenance/fix_wechat_pub_dates.py
  - [x] 遍历所有source='wechat'的文章
  - [x] 随机1-3秒间隔，避免触发微信反爬
  - [x] 自动更新数据库里的published_at字段

- [x] **重新下载补全脚本**
  - [x] scripts/maintenance/redownload_wechat_articles.py
  - [x] 调用fetch_wechat_article_new(url, format='html')重新完整下载
  - [x] 自动补全所有文章的HTML和_files图片文件夹
  - [x] 随机3-8秒间隔，避免触发微信反爬
  - [x] 自动更新数据库的file_path字段

### ✅ 9.3 维护脚本目录重构

- [x] **9个实用maintenance工具分类管理**
  - [x] 006_add_fts_tables.py - FTS5全文检索表重建同步
  - [x] check_articles.py - 文章列表快速查看
  - [x] check_files.py - 文件完整性检查，验证所有数据库记录对应的本地文件是否存在
  - [x] check_schema.py - 数据库Schema查看
  - [x] cleanup_data.py - 孤立冗余文件清理
  - [x] fix_wechat_pub_dates.py - 微信文章发布日期批量修正
  - [x] inspect_db.py - 数据库综合分析（含活跃数统计、软删记录、重复标题检查）
  - [x] purge_deleted.py - 安全永久删除软删记录，带预览确认机制
  - [x] redownload_wechat_articles.py - 全部微信文章重新下载补全图片

- [x] **tests目录专门放临时开发调试/回归测试脚本**
  - [x] test_wechat_time.py - 微信发布时间提取对比测试

---

## Phase 10: 批量操作 & 数据备份恢复 ✅ **2026.5.11 全部完成**

### ✅ 10.1 三库批量操作功能

- [x] **后端批量API** (`backend/api/`)
  - [x] 论文库批量操作 API
  - [x] 文章库批量操作 API
  - [x] 笔记库批量操作 API
  - [x] 支持批量删除、批量打标签、批量改状态

- [x] **前端批量交互**
  - [x] 列表页复选框批量选择
  - [x] 底部批量操作工具栏
  - [x] 批量删除二次确认
  - [x] 批量标签选择弹窗
  - [x] 批量状态切换

### ✅ 10.2 数据备份/恢复功能

- [x] **后端备份服务** (`backend/api/backup.py`)
  - [x] 数据库 + PDF/HTML/笔记文件全量打包
  - [x] 备份文件命名含时间戳
  - [x] 备份列表 API
  - [x] 恢复 API：解压备份包 + 数据库替换

- [x] **前端备份管理**（UI 集成在入库 Tab 页）
  - [x] 一键创建备份按钮
  - [x] 备份历史列表展示
  - [x] 下载备份文件
  - [x] 恢复备份二次确认
  - [x] 删除旧备份

- [x] **SPEC 规约同步** (`specs/`)
  - [x] 备份/恢复 API 接口规约
  - [x] 数据模型规约更新

---

## Phase 11: 入库界面重构 & 交互统一 ✅ **2026.5.12 全部完成**

### ✅ 11.1 入库界面 2x2 分类大卡片布局

- [x] 原来的 7 个 Tab 改为 4 个分类大卡片布局
- [x] 每个卡片代表一类入库方式，视觉层次更清晰
- [x] 卡片图标 + 标题 + 描述，一目了然

### ✅ 11.2 统一三库标签交互体验

- [x] 移除标题行来源标签，内容区底部新增统一标签区域（来源 + 自定义 + 输入框）
- [x] 新增列表页原地增删标签函数，复用通用逻辑
- [x] 修复输入框点击冒泡跳转详情问题（`@click.native.stop` + `@keyup.enter.stop`）
- [x] 统一三库交互：卡片 90% 区域可跳转详情，仅底部交互控件阻止冒泡
- [x] 初始化 `newTagInput` 响应式属性，避免边界问题

### ✅ 11.3 标准化 Vue3 事件处理

- [x] 统一移除 Vue3 事件修饰符 `.native`
- [x] 标准化点击阻止冒泡逻辑
- [x] 所有列表页标签交互完全一致

### ✅ 11.4 入库子页面动态标题

- [x] 入库界面各子页面（arXiv/微信/知乎/笔记等）添加动态标题显示
- [x] 标题随当前选中 Tab 自动切换

---

## Phase 12: 精选内容 & 通用网页提取 ✅ **2026.5.12-5.13 全部完成**

### ✅ 12.1 通用网页正文提取与保存

- [x] 新增入库页「通用网页」Tab
- [x] 集成 trafilatura / readability / newspaper3k 多算法自动选择最佳正文
- [x] 支持任意网页 URL 提取正文保存到文章库
- [x] 支持预览编辑 + 自动保存原始 HTML 文件
- [x] 图片本地化保存，避免外链失效

### ✅ 12.2 精选第三方信息源模块

- [x] 入库页新增「精选第三方信息源」模块
- [x] 支持外链打开与自适应网格布局
- [x] 内置优质信息源快捷入口

### ✅ 12.3 精选公众号模块

- [x] 入库界面新增「精选公众号」Tab，内置宝玉 AI 子页面
- [x] 新增 Excel 转 TXT 脚本 (`scripts/convert_wechat_excel.py`)
  - [x] 按时间倒序生成公众号文章数据
  - [x] 支持增量更新
  - [x] 支持指定公众号名称
- [x] 新增后端分页 API，支持文章列表分页获取（offset/limit），一次返回 100 条
- [x] 封面图自动下载到本地，使用 MD5 命名，避免外链屏蔽问题
- [x] 图片压缩优化：780 张图从 61MB 压缩至 4.5MB，尺寸 240x160、质量 75
- [x] 前端文章卡片展示封面、标题、摘要、发布时间，支持跳转原文
- [x] 新增静态资源路由，提供本地封面图访问服务
- [x] 多公众号图片目录区分，避免不同公众号图片冲突
- [x] 已有图片目录变更兼容处理

### ✅ 12.4 微信文章抓取增强

- [x] 修复代码块、表格渲染问题
- [x] 注入完整美化样式
- [x] 自动降级处理异常页面

---

## Phase 13: 工具箱 & 第三方集成 ✅ **2026.5.29 全部完成**

### ✅ 13.1 工具箱框架搭建

- [x] **独立工具箱页面** (`frontend/toolbox.html`)
  - [x] 左侧导航栏：工具分类列表
  - [x] 右侧内容区：工具详情与操作
  - [x] 与主页面风格一致的 UI 设计
  - [x] 响应式布局适配

### ✅ 13.2 微信读书搜索集成

- [x] **后端服务** (`backend/api/weread.py`)
  - [x] 微信读书 OAuth2 登录流程
  - [x] 书架列表获取 API
  - [x] 书籍详情获取 API
  - [x] 笔记/划线内容获取 API
  - [x] 书籍搜索 API（支持书名/作者/ISBN）

- [x] **前端界面** (`frontend/toolbox_weread.html`)
  - [x] 书架浏览：封面、书名、作者、阅读进度
  - [x] 书籍搜索：关键词实时搜索
  - [x] 笔记查看：按章节展示划线与想法
  - [x] 阅读进度可视化
  - [x] API Key 配置与管理

- [x] **文档**
  - [x] `docs/微信读书搜索使用说明.md` - 完整使用指南

### ✅ 13.3 飞书消息集成

- [x] **后端服务** (`backend/api/feishu.py`)
  - [x] lark-cli 命令行工具集成（支持 user/bot 双身份）
  - [x] 获取用户加入的群聊列表
  - [x] 群聊消息获取（支持分页加载）
  - [x] 消息发送者解析（用户/机器人名称映射）
  - [x] 视频通话消息解析（会议主题、时间、参与者）
  - [x] 消息类型支持：text / image / video_chat / post / file / merge_forward
  - [x] 机器人名称映射表 `BOT_NAME_MAP`
  - [x] 用户名称映射表 `USER_NAME_MAP`

- [x] **前端界面** (`frontend/toolbox_feishu.html`)
  - [x] 群聊选择：我的群聊列表 + 搜索群聊
  - [x] 消息展示：头像、名称、时间、内容
  - [x] 视频通话信息卡片（主题、时间、时长）
  - [x] 批量加载提示（顶部提示条，不遮挡已有消息）
  - [x] 消息时间线分组展示
  - [x] 与主页面风格一致的样式优化

- [x] **文档**
  - [x] `docs/飞书消息功能使用说明.md` - 完整使用指南

### ✅ 13.4 导航与入口统一

- [x] 主页面顶部导航新增「工具箱」入口
- [x] 工具箱页面支持微信读书、飞书消息快速切换
- [x] 各工具页面返回工具箱主页的面包屑导航

---

## Phase 14: 科研辅助工具（长期）

### 📋 14.1 arXiv 版本更新检测

- [ ] 检测 arXiv 论文版本更新
- [ ] 新旧版本保存
- [ ] 版本差异展示（可选）

### 📋 14.2 向量语义检索

- [ ] ChromaDB 集成
- [ ] 文本向量化
- [ ] 语义相似度搜索

---

## 🎯 下一步行动计划（建议优先级）

### 🔥 **高优先级：arXiv 版本更新检测**
- **预计工作量**：1-2 天
- **价值**：自动追踪已入库论文的新版本，避免错过重要更新
- **技术风险**：中，需要定期轮询 arXiv API

### 🟡 **中优先级：向量语义检索**
- **预计工作量**：3-5 天
- **价值**：自然语言搜索，提升知识发现能力
- **技术风险**：中，ChromaDB 本地集成

---

> 💡 **当前项目状态：S 级 - 架构清晰，文档完善，技术债务已清理，Phase 0-13 全部完成！**

*文档最后更新：2026-05-29*
