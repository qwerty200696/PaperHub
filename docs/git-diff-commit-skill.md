# Git Diff Commit 智能提交

## 功能描述

自动分析 Git diff，智能判断提交策略，生成符合 Conventional Commits 规范的中文提交信息。

## 使用方式

```bash
/git-diff-commit
```

## 执行流程

### 1. 检查暂存区状态

首先运行 `git status` 和 `git diff --staged` 检查是否有已暂存（staged）的改动。

#### 情况 A：有 staged 改动

1. **查看 staged diff**：`git diff --staged`
2. **查看 unstaged diff**：`git diff`（未暂存部分）
3. **判断是否合并**：
   - 如果 unstaged 部分与 staged 部分属于**相同功能/模块**，提示用户是否一起提交
   - 如果属于**不同功能**，建议只提交 staged 部分
4. **提交 staged 改动**

#### 情况 B：无 staged 改动

1. **查看所有改动**：`git diff`
2. **分析改动范围**：
   - 单文件小改动 → 直接提交
   - 多文件但属于同一功能 → 一次性提交
   - 多文件且涉及多个独立功能 → 建议分批次提交
3. **询问用户策略**：
   - "检测到 X 个文件改动，涉及 Y 个功能模块"
   - "建议：分 Z 次提交 / 一次性提交"
   - 让用户选择

### 2. 分析改动内容

根据 diff 内容判断 commit type：

| Type | 场景 | 示例 |
|------|------|------|
| `fix` | 修复 bug、错误处理 | `fix(wechat): 修复公众号文章日期解析错误` |
| `feat` | 新功能、新特性 | `feat(feishu): 支持批量加载10次翻页` |
| `docs` | 文档更新 | `docs(api): 更新飞书消息API文档` |
| `style` | 代码格式、样式调整 | `style(css): 优化消息卡片圆角样式` |
| `refactor` | 重构、代码优化 | `refactor(parser): 重构微信文章解析逻辑` |
| `perf` | 性能优化 | `perf(search): 优化全文检索索引性能` |
| `test` | 测试相关 | `test(feishu): 添加离线消息加载测试` |
| `chore` | 构建、依赖、配置 | `chore(deps): 升级 element-plus 到最新版本` |

### 3. 确定 Scope

从改动的文件路径提取 scope：

- `backend/api/feishu.py` → `feishu` 或 `api`
- `frontend/toolbox_feishu.html` → `feishu` 或 `frontend`
- `backend/services/wechat_parser.py` → `wechat` 或 `parser`
- `browser-extension/content.js` → `extension`
- 多个模块 → 用最主要的模块或省略 scope

### 4. 生成 Commit Message

遵循 Conventional Commits 规范：

```
type(scope): 简短的中文描述

可选的详细描述（如果需要）

可选的 footer（如 closes #123）
```

**规则**：
- 第一行不超过 50 个字符
- 使用中文，简洁明了
- 动词开头，如"修复"、"添加"、"优化"、"重构"
- 避免使用"了"、"的"等冗余词

**示例**：
```
✅ fix(feishu): 修复离线消息仅加载50条的问题
✅ feat(feishu): 支持消息按时间正序反序排列
✅ refactor(parser): 优化微信文章日期解析逻辑
❌ fix: 修复了一个bug（太模糊）
❌ feat: 添加了新功能（不明确）
```

### 5. 执行提交

```bash
# 如果有 staged 改动
git commit -m "type(scope): 中文描述"

# 如果需要先 stage
git add <files>
git commit -m "type(scope): 中文描述"
```

### 6. 提交后反馈

- 显示提交 hash
- 提示是否推送到远程
- 如果有未提交的改动，提示后续操作

## 智能判断逻辑

### 分批次 vs 一次性提交

**分批次提交的场景**：
- 改动涉及 3+ 个独立功能模块
- 单个文件改动超过 200 行
- 同时包含功能代码和配置文件的大规模改动

**一次性提交的场景**：
- 单一功能的完整实现
- 相关联的小改动（< 5 个文件）
- 重构但不改变功能的行为

### 示例对话

**场景 1：有 staged 改动**
```
检测到 2 个文件已暂存：
  - backend/api/feishu.py (修改离线消息加载逻辑)
  - frontend/toolbox_feishu.html (调整前端显示)

未暂存改动：
  - docs/README.md (更新文档)

建议：当前 staged 改动属于同一功能（飞书离线消息），可以一起提交。
未暂存的文档更新建议单独提交。

是否提交当前 staged 改动？[Y/n]
```

**场景 2：无 staged 改动，多模块**
```
检测到 8 个文件改动，涉及 3 个模块：
  - feishu: 3 个文件（消息排序、批量加载）
  - wechat: 2 个文件（日期修复）
  - config: 3 个文件（依赖更新）

建议分 3 次提交：
  1. feat(feishu): 支持消息排序和批量加载
  2. fix(wechat): 修复公众号文章日期解析
  3. chore(deps): 升级项目依赖

是否按建议分批提交？[Y/n] 
或者输入 'all' 一次性提交所有改动
```

**场景 3：单文件小改动**
```
检测到 1 个文件改动：
  - backend/api/feishu.py (+15, -3)

建议提交信息：
  fix(feishu): 修复离线消息仅加载50条的问题

是否提交？[Y/n]
```

## 注意事项

1. **始终先展示 diff 摘要**，让用户确认改动范围
2. **提供明确的选项**，不要自动执行危险操作
3. **保留灵活性**，允许用户自定义 commit message
4. **遵循项目规范**，参考 `.gitmessage` 或项目历史提交风格
5. **大改动谨慎处理**，超过 500 行的改动建议用户手动 review

## 相关命令参考

```bash
# 查看状态
git status

# 查看 staged diff
git diff --staged

# 查看 unstaged diff
git diff

# 查看具体文件 diff
git diff <file>

# 暂存文件
git add <file>

# 取消暂存
git reset HEAD <file>

# 提交
git commit -m "message"

# 修改上次提交
git commit --amend
```
