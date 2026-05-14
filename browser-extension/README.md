# PaperHub Browser Extension

PaperHub 浏览器插件 - 一键剪藏网页内容到 PaperHub

## 📦 安装依赖

### 1. 下载 Readability.js

从 Mozilla 官方仓库下载：

```bash
cd browser-extension/lib
curl -o readability.js https://raw.githubusercontent.com/mozilla/readability/master/Readability.js
```

或者手动下载：
- 访问：https://github.com/mozilla/readability/blob/master/Readability.js
- 点击 "Raw" 按钮
- 保存为 `browser-extension/lib/readability.js`

### 2. 准备图标文件

在 `icons/` 目录下放置以下尺寸的 PNG 图标：
- `icon-16.png` (16x16)
- `icon-48.png` (48x48)
- `icon-128.png` (128x128)

可以暂时使用任意 PNG 图片替代，或从 PaperHub Logo 生成。

## 🚀 开发模式加载

### Chrome/Edge 浏览器

1. 打开浏览器，访问 `chrome://extensions/`
2. 开启右上角的 **"开发者模式"**
3. 点击 **"加载已解压的扩展程序"**
4. 选择 `browser-extension` 目录
5. 插件加载成功，工具栏会出现 PaperHub 图标

### Firefox 浏览器

1. 访问 `about:debugging#/runtime/this-firefox`
2. 点击 **"临时载入附加组件"**
3. 选择 `browser-extension/manifest.json`

## 🧪 测试流程

### 1. 启动 PaperHub 后端

```bash
cd /Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/backend
python app.py
```

确保服务运行在 `http://localhost:5799`

### 2. 测试全文剪藏

1. 打开任意网页（如技术博客）
2. 点击浏览器工具栏的 PaperHub 图标
3. **点击右上角 ⚙️ 设置按钮**
4. **确认 API 地址为 `http://localhost:5799`（默认端口）**
5. **点击“💾 保存配置”**
6. 选择 **“全文剪藏”** 模式
7. 点击 **“保存到 PaperHub”**
8. 检查 PaperHub 文章库是否新增该文章

### 3. 测试选择剪藏

1. 在网页上选中一段文字
2. 自动弹出浮动工具栏
3. 点击 **“📝 笔记”** 或 **“📄 文章”**
4. 检查对应库是否保存成功

**注意**：如果点击按钮无反应，请刷新页面后重试（Content Script 需要在页面加载时注入）。

## 📁 项目结构

```
browser-extension/
├── manifest.json          # 插件配置（Manifest V3）
├── popup.html             # 弹窗 UI
├── popup.js               # 弹窗逻辑
├── content.js             # 内容脚本（页面提取）
├── content.css            # 内容脚本样式
├── background.js          # 后台服务
├── icons/                 # 图标文件
│   ├── icon-16.png
│   ├── icon-48.png
│   └── icon-128.png
├── lib/                   # 第三方库
│   └── readability.js     # Mozilla Readability
└── README.md              # 本文件
```

## 🔧 功能特性

### ✅ 已实现

- **全文剪藏**：使用 Readability.js 提取网页正文，保存到文章库
- **选择剪藏**：划词选中内容，快速保存到笔记库或文章库
- **浮动工具栏**：类似语雀的划词工具，支持剪藏/翻译/复制
- **标签支持**：剪藏时可添加自定义标签
- **通知提示**：保存成功/失败的用户反馈
- **⚙️ 后端配置**：支持自定义 PaperHub API 地址和端口
- **🔍 连接测试**：一键测试与后端的连接状态

### 🚧 开发中

- **智能剪藏**：AI 自动提取关键信息（需后端 LLM 支持）
- **速记笔记**：快速编辑器弹窗
- **论文专用剪藏**：arXiv/IEEE/ACM 元数据自动提取
- **OCR 识别**：图片文字提取

## 🐛 常见问题

### 1. 插件图标不显示

检查 `icons/` 目录下是否有正确的 PNG 文件。

### 2. 无法连接到 PaperHub 后端

- 确认后端服务已启动：`http://localhost:5799`
- **点击插件右上角的 ⚙️ 设置按钮**
- **检查 API 地址配置是否正确（默认 `http://localhost:5799`）**
- **⚠️ 重要：修改端口后必须点击“💾 保存配置”才能生效**
- **点击“🔍 测试连接”按钮验证连接状态**
- 如果端口不是 5799，修改为实际端口（如 `http://localhost:8080`）
- 查看浏览器控制台是否有 CORS 错误

### 3. 全文剪藏提取失败

- 某些动态加载的页面可能无法正确提取
- 尝试等待页面完全加载后再剪藏
- 检查控制台错误日志

### 4. 浮动工具栏不出现

- 确认 `content.js` 和 `content.css` 已正确加载
- 检查浏览器控制台是否有 JavaScript 错误
- **刷新页面后重试**（Content Script 只在页面加载时注入）
- 在控制台输入 `console.log(window.PaperHubClipper)` 检查是否已加载

### 5. 点击浮动工具栏按钮无反应

- 确保使用的是最新版本插件（刷新插件后需刷新页面）
- 检查控制台是否有 “Extension context invalidated” 错误
- 如有此错误，关闭所有标签页后重新打开浏览器

## 📝 开发规范

### 代码风格

- 使用 ES6+ 语法
- 函数命名采用 camelCase
- 常量使用 UPPER_SNAKE_CASE
- 添加详细的 JSDoc 注释

### 提交规范

遵循 Conventional Commits：

```bash
feat(extension): 实现全文剪藏功能
fix(extension): 修复浮动工具栏定位问题
docs(extension): 更新安装说明
```

## 🔗 相关文档

- [Mozilla Readability](https://github.com/mozilla/readability)
- [Chrome Extension Manifest V3](https://developer.chrome.com/docs/extensions/mv3/intro/)
- [PaperHub 对标分析文档](../docs/20260514_PaperHub_vs_Zotero对标分析与优化方案.md)

---

*最后更新：2026-05-14*

## 📝 更新日志

### v1.0.0 (2026-05-14)

**核心功能**
- ✅ 实现全文剪藏功能（基于 Readability.js）
- ✅ 实现选择剪藏功能（浮动工具栏）
- ✅ 支持保存到文章库和笔记库
- ✅ 后端 API：`/api/ingest/browser_clipper`

**Bug 修复**
- 🔧 修复 Readability.js 未暴露到全局的问题（添加 wrapper）
- 🔧 修复浮动工具栏点击无响应（改用 mousedown 事件）
- 🔧 修复文件路径问题（使用 BASE_DIR 绝对路径）
- 🔧 修复 file_path 存储格式（改为相对路径 `web/filename.html`）
- 🔧 修复 URL 特殊字符导致文件名截断（清理 # ? & 等字符）
- 🔧 修复 Article 模型字段名错误（original_url → url 等）
- 🔧 修复 Note 模型字段名错误（source_url → url）
- 🔧 修复 Note 创建时 id 类型不匹配问题
- 🔧 修复日期类型转换（ISO 字符串 → Python date 对象）
- 🔧 修复模块导入兼容性（try-except 处理 BASE_DIR）
- 🔧 修复选择剪藏 API 调用（统一使用 browser_clipper 接口）
- 🔧 修复 CORS 跨域问题（允许所有来源）

**功能优化**
- ✨ 支持自定义后端 API 地址和端口
- ✨ 添加连接测试功能
- ✨ 默认端口改为 5799（与后端一致）
- ✨ 添加详细的调试日志
- ✨ 优化错误提示信息
