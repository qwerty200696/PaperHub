# PaperHub

> 本地化、私有化的论文·文章·笔记一体化知识管理系统，专为算法工程师设计。

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/backend-Flask-brightgreen.svg)](https://flask.palletsprojects.com/)
[![Vue 3](https://img.shields.io/badge/frontend-Vue%203-42b883.svg)](https://vuejs.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## ✨ 特性

- **三库一体** — 论文库、文章库、笔记库，一致的标签/状态/筛选体验
- **多源入库** — arXiv 论文 / 微信公众号 / 知乎专栏 / 通用网页 / AI 对话笔记，一键导入
- **本地优先** — 所有数据存储在本地 SQLite + 文件系统，隐私安全，永久可用
- **全文检索** — SQLite FTS5 实现，300ms 防抖搜索，支持拼音排序
- **AI 解读** — 一键调用大模型生成论文/文章解读笔记，支持多模型提供商
- **统一渲染** — PDF 原生预览 / HTML iframe 渲染 / Markdown 高亮展示

## 📸 截图

*(待补充)*

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js（可选，仅前端开发时）

### 安装

```bash
cd PaperHub/backend
pip install -r requirements.txt
```

### 启动

```bash
cd PaperHub/backend
python app.py
```

浏览器打开: http://localhost:5000

## 📂 项目结构

```
PaperHub/
├── backend/                # Flask 后端服务
│   ├── app.py              # 主入口
│   ├── config.py           # 配置管理
│   ├── api/                # API 路由
│   ├── services/           # 业务逻辑（抓取、解析、去重等）
│   └── models/             # 数据模型
├── frontend/               # 前端应用 (Vue 3 + Element Plus, CDN)
│   ├── index.html          # 主应用 (~4000 行单文件)
│   ├── toolbox.html        # 工具箱入口
│   └── src/
│       ├── css/style.css   # 全局样式
│       └── modules/        # 功能模块
├── data/                   # 数据存储
│   ├── papers/             # PDF/HTML/MD 原文
│   ├── db/                 # SQLite 数据库
│   ├── backups/            # 备份文件
│   └── feishu_messages/    # 飞书消息缓存
├── tools/                  # 第三方工具脚本
│   ├── agnes_image.py      # Agnes 图像生成 API
│   └── agnes_video.py      # Agnes 视频生成 API
├── scripts/                # 维护与调试工具
│   ├── maintenance/        # 长期维护脚本
│   └── tests/              # 临时开发/测试脚本
└── docs/                   # 开发文档
```

## 📖 核心功能

### 论文库
- arXiv 论文自动抓取、本地 PDF 上传
- PDF 在线预览（翻页/缩放）
- 阅读状态管理（待读 / 在读 / 已读 / 精读）
- 二级分类 + 全文检索 + 多维度筛选

### 文章库
- 微信公众号 / 知乎专栏 / 通用网页一键导入
- 微信文章 HTML 还原渲染（完整保留样式、图片本地化）
- 独立标签系统、状态管理

### 笔记库
- Markdown 完整渲染（语法高亮、代码块、表格）
- 图片 Ctrl+V 粘贴上传
- 智能标签同步（自动关联论文/文章标签）
### 工具箱

- **微信读书** — 书籍搜索 / 书评 / 热门划线 / 分享卡片
- **飞书消息** — 群聊历史消息拉取、离线查看、智能发送者识别
- **60s 信息流看板** — 热搜、AI 资讯、摸鱼日报、金价油价等 18 个信息源一站式聚合
- **时光清单** — 待办管理 / 日历视图 / 番茄钟 / 纪念日倒数
- 更多工具持续更新中... 🚧

## ⚙️ 配置

复制 `.env.example` 为 `.env`，按需填入 API Key：

```bash
cp .env.example .env
```

## 📄 文档

- [PLAN.md](./PLAN.md) — 详细规划
- [CHECKLIST.md](./CHECKLIST.md) — 实施进度
- [docs/](./docs/) — 技术文档（架构设计、踩坑记录等）

## 🛠 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Flask + SQLite + SQLAlchemy |
| 解析 | BeautifulSoup4 + requests + trafilatura |
| PDF | PyMuPDF (fitz) |
| 前端 | Vue 3 + Element Plus (CDN) |
| 搜索 | SQLite FTS5 |

## 📝 License

MIT
