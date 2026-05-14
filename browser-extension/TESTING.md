# PaperHub 浏览器插件 - 快速测试指南

## 🚀 立即开始测试

### 第一步：加载插件到浏览器

1. **打开 Chrome/Edge 浏览器**
2. 访问 `chrome://extensions/`
3. 开启右上角 **"开发者模式"**
4. 点击 **"加载已解压的扩展程序"**
5. 选择目录：`/Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/browser-extension`
6. ✅ 插件加载成功，工具栏出现紫色 "P" 图标

### 第二步：启动 PaperHub 后端

```bash
cd /Users/wanglijie/PycharmProjects/claude_code_project/PaperHub/backend
/opt/anaconda3/envs/py38/bin/python app.py
```

确认服务运行在 `http://localhost:5000`

### 第三步：测试全文剪藏

1. **打开任意网页**（推荐技术博客，如 Medium、知乎专栏）
2. 点击浏览器工具栏的 **PaperHub "P" 图标**
3. 弹窗显示当前页面标题和 URL
4. 确保选择 **"📄 全文剪藏"** 模式（默认）
5. （可选）在标签输入框添加标签，如：`技术, AI`
6. 点击 **"💾 保存到 PaperHub"**
7. 等待提示 "✅ 保存成功！"
8. 打开 PaperHub 前端 `http://localhost:5000`，检查 **文章库** 是否新增该文章

### 第四步：测试选择剪藏

1. **打开任意网页**
2. **鼠标选中一段文字**（至少 10 个字符）
3. 自动弹出浮动工具栏（白色背景，带阴影）
4. 点击 **"📝 笔记"** 或 **"📄 文章"** 按钮
5. 右上角显示通知："✅ 已保存到笔记库" 或 "✅ 已保存到文章库"
6. 打开 PaperHub 前端，检查对应库是否保存成功

---

## 🧪 测试场景清单

### ✅ 基础功能测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|---------|---------|------|
| 插件加载 | chrome://extensions/ 加载 | 图标出现在工具栏 | ⏳ |
| 弹窗打开 | 点击插件图标 | 显示页面信息和剪藏模式 | ⏳ |
| 全文提取 | 选择"全文剪藏"并保存 | 文章库新增记录 | ⏳ |
| 选择剪藏-笔记 | 选中文本 → 点击"笔记" | 笔记库新增记录 | ⏳ |
| 选择剪藏-文章 | 选中文本 → 点击"文章" | 文章库新增记录 | ⏳ |
| 标签添加 | 输入标签后保存 | 保存的内容包含标签 | ⏳ |
| 重复检测 | 同一 URL 保存两次 | 第二次提示"已存在" | ⏳ |

### 🔍 边界情况测试

| 测试项 | 操作步骤 | 预期结果 | 状态 |
|--------|---------|---------|------|
| 空标题页面 | 在无标题页面剪藏 | 使用 URL 作为标题 | ⏳ |
| 动态加载页面 | 在 SPA 页面剪藏 | 等待加载后正确提取 | ⏳ |
| 无正文页面 | 在首页/列表页剪藏 | 提示"无法提取内容" | ⏳ |
| 未选中文字 | 直接点击浮动工具栏 | 提示"请先选中内容" | ⏳ |
| 后端未启动 | 后端关闭时保存 | 提示"无法连接到后端" | ⏳ |

---

## 🐛 常见问题排查

### 问题 1：插件图标不显示

**原因**：图标文件缺失或 manifest.json 配置错误

**解决**：
```bash
# 检查图标文件是否存在
ls -la browser-extension/icon-*.png

# 如果缺失，重新生成
/opt/anaconda3/envs/py38/bin/python browser-extension/generate_icons.py
```

### 问题 2：点击插件图标无反应

**原因**：popup.html 加载失败

**解决**：
1. 右键点击插件图标 → "检查弹出内容"
2. 查看控制台错误信息
3. 常见错误：
   - `Failed to load resource`: 检查文件路径
   - `Uncaught ReferenceError`: 检查 popup.js 语法

### 问题 3：全文剪藏提取失败

**原因**：Readability.js 无法识别页面结构

**解决**：
1. 打开浏览器控制台（F12）
2. 查看是否有 `[PaperHub Clipper] Extraction failed` 错误
3. 尝试其他网页（推荐博客文章，避免首页/列表页）
4. 等待页面完全加载后再剪藏

### 问题 4：浮动工具栏不出现

**原因**：content.js 未正确注入或 CSS 冲突

**解决**：
1. 刷新页面
2. 重新加载插件（chrome://extensions/ → 刷新按钮）
3. 检查控制台是否有 content.js 错误
4. 确认选中了至少 10 个字符的文本

### 问题 5：保存失败 - 无法连接到后端

**原因**：PaperHub 后端未启动或端口不对

**解决**：
```bash
# 检查后端是否运行
curl http://localhost:5000/api/papers?page=1&per_page=1

# 如果返回 404/500，重启后端
cd backend
/opt/anaconda3/envs/py38/bin/python app.py
```

### 问题 6：CORS 错误

**原因**：浏览器跨域限制

**解决**：
1. 检查 `manifest.json` 中的 `host_permissions` 是否包含 `http://localhost:5000/*`
2. 确认后端 Flask 启用了 CORS（应该已配置）
3. 尝试在 `background.js` 中添加 CORS headers

---

## 📊 调试技巧

### 查看 Content Script 日志

1. 打开任意网页
2. F12 打开开发者工具
3. 切换到 **Console** 标签
4. 筛选关键词：`[PaperHub Clipper]`

### 查看 Background Script 日志

1. 访问 `chrome://extensions/`
2. 找到 PaperHub Clipper
3. 点击 **"service worker"** 链接
4. 查看后台服务日志

### 查看 Popup 日志

1. 右键点击插件图标
2. 选择 **"检查弹出内容"**
3. 查看弹窗的控制台日志

### 网络请求监控

1. F12 打开开发者工具
2. 切换到 **Network** 标签
3. 执行剪藏操作
4. 查看发送到 `http://localhost:5000/api/ingest/browser_clipper` 的请求
5. 检查 Request Payload 和 Response

---

## 🎯 下一步优化方向

### 短期（本周）

- [ ] 修复已知的边界情况 Bug
- [ ] 优化 Readability 提取成功率
- [ ] 添加更多错误提示和用户引导

### 中期（1 个月内）

- [ ] 实现智能剪藏（AI 提取关键信息）
- [ ] 实现速记笔记（快速编辑器）
- [ ] 支持论文专用剪藏（arXiv/IEEE/ACM）

### 长期（3 个月内）

- [ ] OCR 图片文字识别
- [ ] 批量剪藏（一次保存多个标签页）
- [ ] 离线缓存支持
- [ ] 发布到 Chrome Web Store

---

## 📞 反馈与支持

遇到问题或有建议？

1. 查看浏览器控制台日志
2. 检查 [README.md](./README.md) 常见问题
3. 提交 Issue 到 GitHub

---

*最后更新：2026-05-14*  
*MVP 版本：v1.0.0*
