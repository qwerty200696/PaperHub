# PaperHub 前端经典 Bug 汇总与避坑指南

---

## 💊 前言

> **90% 的前端 Bug 都是低级错误造成的，10 分钟排查，1 秒钟修复**

本文件记录 PaperHub 开发过程中踩过的所有前端坑，以及对应的快速排查方法，避免以后重复踩。

---

## 🐛 Bug #1: watch is not defined

**发生时间**：2026-05-02
**发现者**：用户

### 现象
- 页面完全空白，不显示任何论文、文章、笔记
- 所有功能都没反应，看起来像网站挂了

### F12 报错
```
Uncaught ReferenceError: watch is not defined
    at setup (index.html:1628)
```

### 根本原因
```javascript
// ❌ 新增了 watch 用法，但忘了导入
const { createApp, ref, computed, onMounted } = Vue;

// 后面代码用了 watch()
watch(noteSortBy, (newVal) => { ... });

// ✅ 修复
const { createApp, ref, computed, onMounted, watch } = Vue;
```

### 根因分析
1. Vue 3 组合式 API 每一个函数都要显式从 Vue 解构出来
2. `ref`/`computed` 用的多一般不会忘，但 `watch`/`nextTick` 等偶尔用就容易忘
3. JS 执行到 `watch()` 就直接崩溃，整个 App 停止挂载，页面全白

### ✅ 快速排查 Checklist
- [ ] 有没有加新的 Vue API？
- [ ] 开头解构的地方对应加上了吗？
- [ ] F12 控制台是不是有红色的 `xxx is not defined`？

### ⏱️ 排查时间 vs 修复时间
- **排查**: 10 分钟
- **修复**: 1 秒钟
- **坑指数**: ⭐⭐⭐⭐⭐

---

## 🐛 Bug #2: 修改了详情页数据，列表页不变

**发生时间**：2026-05-02
**发现者**：用户

### 现象
- 点击「待读」的笔记/文章，进入详情页
- 详情页状态变成「在读」了
- 回到列表，显示还是「待读」
- 刷新页面才会显示正确

### 根本原因
**Vue 响应式是基于对象引用的**：

```javascript
async function viewNoteDetail(note) {
    // 这个只是详情页的对象！
    viewingNote.value = note;
    
    if (viewingNote.value.status === 'pending') {
        viewingNote.value.status = 'reading';  // ❌ 只改了详情页对象
        await updateNoteStatus(viewingNote.value);
        // 漏掉了！！
        // const idx = allNotes.value.findIndex(n => n.id === note.id);
        // allNotes.value[idx].status = 'reading';  // ✅ 必须同时修改列表数组！
    }
}
```

### 根因分析
用户在列表看到的是 `papers`/`allArticles`/`allNotes` 数组里的对象，不是详情页的 `selectedPaper`/`viewingArticle`/`viewingNote` 对象！

改一个，另一个不会自动同步，因为是两个不同的对象引用。

### ✅ 快速排查 Checklist
- [ ] 是不是只改了详情页对象？
- [ ] 列表对应的数组同步更新了吗？
- [ ] 是不是刷新就对，不刷新就不对？

### ⏱️ 排查时间 vs 修复时间
- **排查**: 5 分钟
- **修复**: 3 行代码
- **坑指数**: ⭐⭐⭐⭐

---

## 🐛 Bug #3: Element Plus 组件点击事件不生效

**发生时间**：2026-04-28
**发现者**：开发中

### 现象
```html
<el-tag closable @close="removeTag">标签</el-tag>
```
点击 X 关闭按钮，事件不触发！

### 根本原因
Element Plus 组件自定义事件需要加 `.native` 修饰符！

```html
<!-- ❌ 不生效 -->
<el-tag closable @close="removeTag">

<!-- ✅ 生效 -->
<el-tag closable @close.native="removeTag">
```

### ✅ 速查清单
| 组件 | 事件 | 需要 .native 吗？ |
|------|------|----------------|
| el-tag | @click | 是！ |
| el-tag | @close | 是！ |
| el-button | @click | 不用 |
| el-select | @change | 不用 |

**记忆口诀**：原生 HTML 元素有的事件，组件包装后就需要 `.native`！

---

## 🐛 Bug #4: localStorage 存的是字符串 "[object Object]"

**发生时间**：2026-04-27
**发现者**：开发中

### 现象
刷新页面前筛选状态正常，刷新后全乱了

### 根本原因
```javascript
// ❌ 存对象进去
localStorage.setItem('filter', filterObject);

// 存进去变成了 "[object Object]"
localStorage.getItem('filter');  // → "[object Object]"

// ✅ 序列化
localStorage.setItem('filter', JSON.stringify(filterObject));

// ✅ 取出来反序列化
const filter = JSON.parse(localStorage.getItem('filter') || '{}');
```

### 💡 教训
**localStorage 只能存字符串！** 传对象进去会自动调用 `.toString()`，变成垃圾数据。

---

## 🐛 Bug #5: CDN 模式下 ES Module 跨域问题

**发生时间**：2026-04-25
**发现者**：模块化重构时

### 现象
- IDE 里双击打开 index.html
- file:// 协议打开
- `import()` 动态加载模块报 CORS 错误

### 根本原因
浏览器 file:// 协议不支持 ES Module 跨域导入：

```javascript
// ❌ file:// 打开会报错
import('/src/modules/tagModule.js').then(...)
```

### 解决方案
1. 所有模块内联到 index.html，不拆分
2. 或者永远用 `http://localhost:5000` 访问，不要直接双击打开

---

## 🐛 Bug #6: Element Plus el-dialog 放在嵌套 div 内部无法显示

**发生时间**：2026-05-04  
**发现者**：用户（AI 解读功能的设置按钮）

### 现象
- 点击按钮，函数执行正常，`console.log` 输出正常
- 响应式变量 `aiConfigDialogVisible` 确实变成了 `true`
- 但是 **屏幕上看不到任何弹窗**

### 根本原因
`el-dialog` 组件放在了嵌套很深的 div 内部（比如论文详情页里面），Element Plus 的弹窗机制需要正确的 DOM 层级关系。

```html
<!-- ❌ 错误示范 -->
<div id="app">
    <div v-if="activeMenu === 'papers'">
        <div v-if="selectedPaper">
            <!-- 论文详情内容 -->
            ...
            
            <!-- 弹窗放在这里！嵌套太深 -->
            <el-dialog v-model="aiConfigDialogVisible">
                ...
            </el-dialog>
        </div>
    </div>
</div>
```

### 正确做法
弹窗组件必须放在 `#app` 的**直接子元素**位置：

```html
<!-- ✅ 正确示范 -->
<div id="app">
    <!-- 所有内容区域 -->
    <div v-if="activeMenu === 'papers'">
        ...
    </div>
    
    <!-- 弹窗全部放在最外层 -->
    <el-dialog v-model="aiConfigDialogVisible">
        ...
    </el-dialog>
    <el-dialog v-model="noteEditorVisible">
        ...
    </el-dialog>
</div>
```

### ✅ 快速排查 Checklist
- [ ] 弹窗是不是在某个 `v-if` 包裹的区域里面？
- [ ] 弹窗是不是嵌套在几层 div 下面？
- [ ] 试着把弹窗移到 `#app` 最下面试试？

### ⏱️ 排查时间 vs 修复时间
- **排查**：30 分钟（先试了 z-index、事件绑定、甚至写了测试函数）
- **修复**：2 分钟（剪切粘贴到外层）
- **坑指数**: ⭐⭐⭐⭐⭐

---

## 🐛 Bug #7: Element Plus el-divider 不显示导致按钮消失

**发生时间**：2026-05-04  
**发现者**：用户（论文详情页 AI 解读按钮）

### 现象
- 页面上能看到分隔符 `|`，但分隔符后面的按钮完全看不见
- 代码检查完全正确，按钮的 HTML 都在
- 用 Chrome DevTools 也看不到按钮元素

### 根本原因
`el-divider` 组件在某些布局环境下渲染异常，导致后续元素被隐藏或脱离文档流。

### 排查过程
1. ✅ 检查函数是否正确暴露到 return → 正确
2. ✅ 检查函数是否正确定义 → 正确
3. ✅ 尝试把按钮移到其他位置 → 仍然不显示
4. ❌ 最后发现是 `el-divider` 的问题

### 正确做法
用简单的文本分隔符替代 `el-divider`：

```html
<!-- ❌ 可能不显示 -->
<el-divider direction="vertical" />
<el-button>按钮A</el-button>
<el-button>按钮B</el-button>

<!-- ✅ 用文本分隔符更可靠 -->
<span style="color: #E4E7ED; margin: 0 4px;">|</span>
<el-button>按钮A</el-button>
<el-button>按钮B</el-button>
```

### ✅ 快速排查 Checklist
- [ ] 是不是用了 `el-divider`？
- [ ] 尝试换成文本分隔符 `|` 看看？
- [ ] 按钮的父容器有没有特殊样式？

### ⏱️ 排查时间 vs 修复时间
- **排查**：20 分钟（排除各种可能）
- **修复**：1 分钟（改分隔符字符）
- **坑指数**: ⭐⭐⭐⭐

---

## 🐛 Bug #8: 添加新控件后原有按钮被挤到不可见区域

**发生时间**：2026-05-05  
**发现者**：用户（论文详情页标星按钮消失）

### 现象
- 列表页有标星按钮，详情页没有
- 添加"保存PDF到本地"开关后，标星按钮消失了
- 状态栏只显示：阅读状态、保存PDF到本地两个选项

### 根本原因
在 `flex-wrap: wrap` 的布局容器中添加新控件后，原有按钮被挤到第二行或不可见区域。

```html
<!-- ❌ 标星按钮被挤到后面看不见 -->
<div style="display: flex; flex-wrap: wrap;">
    <span>阅读状态：</span>
    <el-select ... />
    <span>保存PDF到本地：</span>  <!-- 新增的控件 -->
    <el-switch ... />
    <el-button>下载PDF</el-button>
    <el-button>标星</el-button>  <!-- 被挤到看不见 -->
    ...
</div>
```

### 正确做法
把常用按钮移到更靠前的位置：

```html
<!-- ✅ 标星按钮移到前面 -->
<div style="display: flex; flex-wrap: wrap;">
    <span>阅读状态：</span>
    <el-select ... />
    <el-button>标星</el-button>  <!-- 移到前面 -->
    <span>|</span>
    <span>保存PDF到本地：</span>
    <el-switch ... />
    <el-button>下载PDF</el-button>
    ...
</div>
```

### ✅ 快速排查 Checklist
- [ ] 是不是刚添加了新控件？
- [ ] 父容器有没有 `flex-wrap: wrap`？
- [ ] 把消失的按钮移到前面试试？

### ⏱️ 排查时间 vs 修复时间
- **排查**：5 分钟（确认按钮代码存在，布局问题）
- **修复**：2 分钟（调整按钮顺序）
- **坑指数**: ⭐⭐⭐

---

## 🐛 Bug #9: Element Plus el-switch 自闭合标签导致后续元素不显示

**发生时间**：2026-05-06  
**发现者**：用户（论文详情页下载PDF、配置、AI解读按钮消失）

### 现象
- 在 `el-switch` 组件后面添加的按钮全部不显示
- 代码检查完全正确，按钮的 HTML 都在
- 只有 `el-switch` 前面的元素能正常显示

### 根本原因
Element Plus 的 `el-switch` 组件使用**自闭合标签** `/>` 时，可能导致后续兄弟元素不渲染。

```html
<!-- ❌ 自闭合标签导致后续元素不显示 -->
<el-switch
    v-model="selectedPaper.save_local"
    :disabled="!selectedPaper.url"
    @change="updateSaveLocal(selectedPaper, selectedPaper.save_local)"
    active-text="是"
    inactive-text="否"
/>
<el-button type="primary">下载PDF</el-button>  <!-- 不显示！ -->
<el-button>配置</el-button>  <!-- 不显示！ -->
```

### 正确做法
使用**成对标签** `></el-switch>`：

```html
<!-- ✅ 成对标签，后续元素正常显示 -->
<el-switch
    v-model="selectedPaper.save_local"
    :disabled="!selectedPaper.url"
    @change="updateSaveLocal(selectedPaper, selectedPaper.save_local)"
    active-text="是"
    inactive-text="否"
></el-switch>
<el-button type="primary">下载PDF</el-button>  <!-- 正常显示！ -->
<el-button>配置</el-button>  <!-- 正常显示！ -->
```

### 排查过程
1. ✅ 检查后端 API → 数据正确返回 `file_size`
2. ✅ 检查前端条件渲染 → 条件正确
3. ✅ 把文件大小放到标签文本中 → 显示了，但后续按钮消失
4. ❌ 最后发现是 `el-switch` 自闭合标签的问题

### ✅ 快速排查 Checklist
- [ ] 是不是用了 `el-switch` 自闭合标签 `/>`？
- [ ] 后续元素是否不显示？
- [ ] 尝试改成成对标签 `></el-switch>` 试试？

### 📋 全局排查结果

对 `index.html` 进行全局排查后发现：

| 组件 | 是否需要修复 | 原因 |
|------|-------------|------|
| `el-switch` | ✅ **需要** | 后面有兄弟元素（按钮），自闭合会导致后续元素不显示 |
| `el-badge` | ❌ 不需要 | 内联在 `<span>` 中，后面没有兄弟元素 |
| `el-empty` | ❌ 不需要 | 在 `<div>` 内单独使用，后面没有兄弟元素 |
| `el-input` | ❌ 不需要 | 都在 `el-form-item` 内，后面没有兄弟元素 |

**触发条件**：只有当自闭合标签**后面有兄弟元素**时才会导致后续元素不显示。如果自闭合标签是父元素的最后一个子元素，则不会有问题。

### ⏱️ 排查时间 vs 修复时间
- **排查**：30 分钟（排查后端、前端条件渲染、数据加载）
- **修复**：1 秒钟（改成成对标签）
- **坑指数**: ⭐⭐⭐⭐⭐

---

## 🚑 前端 Bug 快速排查万能公式

### Step 1: 浏览器 F12 看报错

红色报错 → 直接定位到某一行
灰色报错 → 一般是网络或业务逻辑问题

### Step 2: 确认「三不一要」

- 不乱点 → 现象描述清楚再动手
- 不乱改 → 先分析再改代码
- 不猜 → 有疑问打日志确认
- 要回滚 → 改完不对马上恢复

### Step 3: 还是不行？

**注释掉刚加的代码，一行一行放开！**
- 注释完就好了 → 说明刚写的代码有问题
- 注释完还不好 → 说明之前就有问题

---

## 📝 防坑 Coding 原则

### ✅ 原则 1: 加新 API 先检查导入
> 加完 `watch(xxx)` 第一反应：开头导入 `watch` 了吗？

### ✅ 原则 2: 修改数据先想「用户在哪看」
> 用户在列表看到的不是详情页的对象！

### ✅ 原则 3: Element Plus 事件先加 .native
> 不生效再删掉

### ✅ 原则 4: localStorage 先 JSON.stringify
> 只要不是字符串，先序列化再说

### ✅ 原则 5: 写 10 行代码测一次
> 不要写 100 行再运行，到时候出问题都不知道是哪一行的锅

---

## 💊 最后一句话

> **前端没有高深的 Bug，只有忘了导入、忘了同步、忘了序列化的坑。**

*文档创建：2026-05-02*
*累计收录 9 个经典坑*
