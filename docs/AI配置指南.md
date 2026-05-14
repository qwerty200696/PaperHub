# AI 配置指南

## 问题描述

点击 AI 解读模块的"配置"按钮时，应该显示已有的默认配置。如果出现 `POST /api/ai/summary HTTP/1.1" 500` 错误，通常是因为 API Key 未正确配置。

## 解决方案

### 1. 配置 .env 文件（推荐）

在项目根目录的 `.env` 文件中配置您的 API Key：

```bash
# LLM API 配置文件

# API Key（必填）- 替换为您的真实 API Key
LLM_API_KEY=your-real-api-key-here

# 默认提供商（可选，默认 doubao）
# 可选值: doubao, openai, anthropic, qwen, teg
LLM_PROVIDER=doubao

# 自定义 API 基础 URL（可选）
# 用于使用代理或私有部署的 API
LLM_BASE_URL=

# 自定义模型（可选）
LLM_MODEL=
```

**支持的提供商：**
- `doubao` - 豆包（默认）
- `openai` - OpenAI (GPT)
- `anthropic` - Claude
- `qwen` - 通义千问
- `teg` - TEG 自定义模型

### 2. 通过前端界面配置

如果不想修改 `.env` 文件，可以通过前端界面配置：

1. 在 AI 解读模块点击"⚙️ 配置"按钮
2. 选择 API 提供商
3. 输入 API Key
4. （可选）填写 Base URL 和 Model ID
5. 点击保存

配置会同时保存到：
- **后端**：内存中（重启后失效）
- **前端 localStorage**：持久化保存

### 3. 验证配置是否生效

配置完成后，尝试点击"生成 AI 解读"按钮：
- ✅ 成功：显示 AI 生成的摘要
- ❌ 失败：检查控制台错误信息

## 常见错误

### 500 错误 - API Key 未配置

**症状：**
```
POST /api/ai/summary HTTP/1.1" 500 -
```

**原因：**
- `.env` 文件中的 `LLM_API_KEY` 仍是占位符 `your-api-key-here`
- 或者前端未配置 API Key

**解决：**
1. 编辑 `.env` 文件，填入真实的 API Key
2. 重启后端服务
3. 或通过前端界面配置 API Key

### 配置弹窗显示为空

**原因：**
- localStorage 中没有保存的配置
- 后端也未配置 API Key
- **或者存在异步加载时序问题**（已修复）

**解决：**
1. 按上述方法配置 API Key
2. **刷新浏览器页面**（清除缓存后需要重新加载）
3. 再次打开配置弹窗即可看到已保存的配置

**技术说明：**
之前存在一个 bug：弹窗打开时，会先调用 `loadAIConfig()` 异步从后端加载配置，但紧接着会用旧的空配置覆盖编辑变量。现已修复，确保：
- 先从 localStorage 同步加载并显示配置
- 再从后端异步加载最新配置并更新显示

## 获取 API Key

### 豆包 (Doubao)
访问 [火山引擎](https://www.volcengine.com/) 注册并创建 API Key

### OpenAI
访问 [OpenAI Platform](https://platform.openai.com/) 创建 API Key

### 通义千问 (Qwen)
访问 [阿里云 DashScope](https://dashscope.aliyun.com/) 创建 API Key

### Anthropic (Claude)
访问 [Anthropic Console](https://console.anthropic.com/) 创建 API Key

## 注意事项

1. **安全性**：不要将 `.env` 文件提交到 Git 仓库（已在 `.gitignore` 中排除）
2. **优先级**：前端配置 > 环境变量 > .env 文件
3. **持久化**：前端配置保存在浏览器 localStorage，清除浏览器数据会丢失
4. **重启影响**：仅通过 `.env` 或环境变量配置的会在重启后保留
