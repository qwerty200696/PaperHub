# PaperHub 开发提示词完全指南

&gt; 本指南为 PaperHub 项目定制，确保所有开发工作严格遵循项目已建立的完整 SPEC 规约体系。

---

## 第一部分：新需求开发标准提示词

### 1.1 基础版提示词（日常开发使用）

```
【PaperHub 新需求开发提示词】
项目根目录：./PaperHub/
前置约束：
1.  命名规范：严格遵循 PaperHub/specs/naming.spec.md
    - 文件/接口/数据库字段：snake_case
    - 前端工具函数：小驼峰 camelCase
    - 类名：帕斯卡 PascalCase
2.  接口响应格式：严格遵循 PaperHub/specs/api_response.spec.md
    - 统一格式：{"code": 状态码, "data": 响应数据, "msg": 提示信息}
    - 状态码参考 specs/system/global_error_codes.yml
3.  架构分层：严格遵循 PaperHub/specs/architecture.spec.md
    - 后端分层：backend/api/ → backend/services/ → backend/models/
    - 前端分层：单页应用 index.html + src/modules/ 工具模块
4.  先读规约再动手！开发前先确认对应模块的现有 SPEC 规约文件

需求描述：
【在这里粘贴你的具体新需求描述】

请按以下步骤执行：
① 先探索项目现有相关代码结构，理解上下文
② 参考已有的 SPEC 规约文件，确保完全符合规范
③ 实现功能，保持代码风格与现有项目一致
④ 关键地方添加注释说明业务逻辑
⑤ 最后运行 git status 确认改动范围
```

### 1.2 完整版提示词（复杂功能开发）

```
【PaperHub 复杂需求完整开发流程】

第一步：规约对齐检查
- 读取 PaperHub/specs/ 目录下所有相关规约文件
- 确认：naming.spec.md（命名）、api_response.spec.md（响应格式）、architecture.spec.md（分层）
- 确认后端相关规约：backend/api/、backend/models/、backend/services/ 下的对应yml
- 确认前端相关规约：frontend/pages/、frontend/modules/ 下的对应yml
- 确认系统规约：system/global_error_codes.yml、system/global_config.yml

第二步：需求分析与设计
- 明确输入输出边界
- 明确接口路径（RESTful风格，复数资源）
- 明确数据库字段命名（snake_case）
- 明确响应超时约束（普通≤300ms，复杂≤2000ms）

第三步：代码实现
- 严格按架构分层实现，不跨层污染
- 后端 Flask 代码风格与现有文件保持一致
- 前端 Vue3 + Element Plus 保持现有代码风格
- 所有标签全闭合，CSS 统一引用 src/css/style.css
- 异常处理覆盖所有边界场景

第四步：自检清单
□ 所有命名都是 snake_case（除了前端工具函数小驼峰）
□ 所有接口响应都是 {"code": 状态码, "data": {}, "msg": ""} 格式
□ 分层正确，API层不写业务逻辑
□ 没有引入新的大驼峰文件名
□ 主键统一为 id，时间字段统一为 created_at / updated_at

需求描述：
【你的复杂功能需求描述】
```

---

## 第二部分：后续规约开发提示词

### 2.1 新增后端API规约提示词

```
【PaperHub 新增后端API SPEC规约生成提示词】
目标目录：PaperHub/specs/backend/api/
输出格式：YAML，直接保存为 .yml 文件
要求：
1.  参考已有的同目录下其他yml文件作为格式模板
2.  每个接口完整包含：
   - api：接口路径，RESTful风格，小写+斜杠，资源复数
   - method：GET/POST/PUT/DELETE
   - desc：清晰的接口功能描述
   - input：请求参数（类型、默认值、是否可选）
   - output：响应数据格式，明确code状态码
   - errors：错误码及对应场景
   - rules：接口业务规则，响应时间约束
3.  所有参数命名 snake_case
4.  响应时间符合约束：普通接口≤300ms，复杂AI/入库接口≤2000ms
5.  先读取项目现有对应API的实际代码，确保规约100%贴合实际业务逻辑

要生成的新API模块名称：【你的模块名，如xxx_manage】
```

### 2.2 新增后端数据模型规约提示词

```
【PaperHub 新增数据模型SPEC规约生成提示词】
目标目录：PaperHub/specs/backend/models/
输出格式：YAML
要求：
1.  参考同目录下 paper.yml 作为格式模板
2.  每个模型完整包含：
   - name：模型名
   - fields：字段名、类型、是否主键、是否唯一、是否可空、备注
   - relations：表关联关系
   - indexes：索引定义（可选）
3.  严格遵循全局字段规范：
   - 主键统一为 id (Integer)
   - 时间字段统一为 created_at、updated_at (DateTime)
   - 外键命名统一为 "关联表名_id"（snake_case）
   - 标题字段 ≤ 512字符，URL字段 ≤ 255字符
4.  先读取 backend/models/paper.py 下实际模型代码，确保规约与代码完全一致

要新增的数据模型名：【你的模型名】
```

### 2.3 新增后端业务服务规约提示词

```
【PaperHub 新增业务服务SPEC规约生成提示词】
目标目录：PaperHub/specs/backend/services/
输出格式：YAML
要求：
1.  参考同目录下其他服务yml作为格式模板
2.  结构完整：
   - service：服务名称
   - description：服务功能描述
   - input：输入参数、类型、约束
   - output：输出数据、格式
   - rules：业务规则、处理步骤、边界约束
   - errors：异常场景及处理方式
3.  只定义"做什么"和"遵循什么规则"，不写具体代码，不限定技术实现
4.  先读取 backend/services/ 目录下对应服务的实际代码，确保贴合业务逻辑

要新增的服务模块名：【你的服务名】
```

### 2.4 新增前端页面规约提示词

```
【PaperHub 新增前端页面SPEC规约生成提示词】
目标目录：PaperHub/specs/frontend/pages/
输出格式：YAML
要求：
1.  参考同目录下 paper_list.yml 作为格式模板
2.  结构完整：
   - page：页面名称
   - elements：页面核心元素清单
   - events：元素触发事件及对应逻辑
   - ui_rules：UI显示规则、样式约束（全闭合标签规范）
   - api_deps：依赖的后端接口列表
   - boundary：边界场景处理（无数据、加载失败、网络错误）
3.  贴合 Vue3 + Element Plus 单页应用特点
4.  统一样式关联到 frontend/src/css/style.css
5.  先读取 frontend/index.html 对应页面的实际代码，确保完全贴合现有实现

要新增的前端页面名：【你的页面名】
```

### 2.5 新增前端工具模块规约提示词

```
【PaperHub 新增前端工具模块SPEC规约生成提示词】
目标目录：PaperHub/specs/frontend/modules/
输出格式：YAML
要求：
1.  参考同目录下 sortUtils.yml 作为格式模板
2.  结构完整：
   - module：模块名称
   - description：模块功能
   - functions：每个函数的 name、input、output、rule
   - constraints：模块使用约束
3.  所有函数命名用小驼峰 camelCase
4.  仅聚焦公共工具函数，不混入页面业务逻辑
5.  约束：所有状态变量通过工厂函数注入，模块内部不自行声明响应式变量
6.  先读取 frontend/src/modules/ 下对应模块的实际JS代码，确保规约100%一致

要新增的工具模块名：【你的模块名】
```

---

## 第三部分：Vibe Coding 规约合规检查提示词

### 3.1 开发中途规约合规巡检提示词

```
【PaperHub 规约中途巡检】
请停下当前开发，执行以下合规检查，不满足的立即修正：

1.  命名规范检查：
    grep 一下所有新写的代码文件，看看有没有出现大驼峰的文件名/接口名/数据库字段名
    除了类名可以帕斯卡，其他必须都是 snake_case（前端工具函数可以小驼峰）
2.  接口响应格式检查：
    所有后端返回的地方，是不是都包装成了 {"code": xxx, "data": xxx, "msg": xxx} 格式？
    有没有漏了直接返回 jsonify(data) 没有包装的情况？
3.  架构分层检查：
    api 目录下的文件有没有直接写复杂业务逻辑？是不是把逻辑都放到 services 层了？
    models 层有没有混入业务逻辑？是不是只做纯数据模型定义？
4.  前端规范检查：
    所有 HTML 标签是不是全闭合？
    新写的样式是不是引用了 style.css 而不是内联随便写？
5.  自检结果输出：列出已通过的项 + 需要修正的项 + 修正动作
```

### 3.2 开发完成最终规约验收提示词

```
【PaperHub 最终规约验收 - 100%通过才能提交】
验收清单：

▨ 命名规范（强制）
□ 所有新文件命名：snake_case（例如 user_profile.py 不是 UserProfile.py）
□ 所有接口路径：snake_case，复数资源（例如 /api/paper_tags 不是 /api/paperTags）
□ 所有数据库字段：snake_case（例如 created_at 不是 createdAt）
□ 前端工具函数：小驼峰（例如 sortByDate 不是 sort_by_date）
□ 类名：帕斯卡命名（例如 PaperService 不是 paper_service）

▨ 接口响应（强制）
□ 所有后端接口统一返回 {"code": 状态码, "data": 数据, "msg": "提示"}
□ 状态码严格参考 specs/system/global_error_codes.yml
□ 没有任何地方直接返回原始数据不包装

▨ 架构分层（强制）
□ backend/api/: 仅做参数校验 + 调用services，无复杂业务逻辑
□ backend/services/: 所有业务逻辑实现位置
□ backend/models/: 仅数据模型定义，零业务逻辑
□ frontend/src/modules/: 纯公共工具函数，无页面业务逻辑

▨ 代码风格（强制）
□ 后端代码与现有 Flask 代码风格 100% 一致
□ 前端代码与现有 Vue3 + Element Plus 风格完全统一
□ 没有引入新的第三方依赖，除非明确说明原因

▨ 边界场景（推荐）
□ 处理了无数据情况
□ 处理了网络失败/异常捕获
□ 有加载状态和错误提示

请输出：全部验收结果，列出通过项和待整改项，整改完成后才能 git commit。
```

### 3.3 Git Commit 前规约快速校验提示词

```
【PaperHub Commit 前规约快速扫描】
执行命令：
cd PaperHub/
git diff --name-only --cached
然后检查这些待提交的改动文件：
1.  有没有不符合 naming.spec.md 的命名？
2.  有没有接口响应格式不统一的地方？
3.  有没有跨层污染架构分层？
4.  扫描完输出结论，有问题先修正再提交，没问题输出 "✅ 规约校验通过，可以 commit"
```

---

## 第四部分：规约新增/迭代通用模板提示词

```
【PaperHub SPEC规约新增/迭代通用模板】
目标：为PaperHub项目新增/更新某一份SPEC规约文档
前置准备：
1.  先探索 PaperHub/specs/ 目录下已有的所有规约，理解整体风格和格式
2.  读取项目实际相关代码文件，100% 贴合实际业务逻辑
3.  禁止写与项目实际无关的冗余内容
生成要求：
- 格式与同目录下已有的规约文件完全保持一致
- 结构完整、明确、无歧义、可验证
- 仅定义"做什么"和"遵循什么规则"，不限制具体实现方式
- 输出文件放到 specs/ 目录下对应正确位置
```

---

## 使用说明

1.  将本指南放在 PaperHub 项目根目录下，随时可以查阅
2.  每次开发新需求前，复制对应提示词作为对话开头
3.  中途用"规约中途巡检"来确保不跑偏
4.  最后开发完成后运行"最终规约验收"
5.  整个开发流程确保 100% 符合项目建立的完整 SPEC 规约体系！
