# PaperHub vs Zotero 对标分析与优化方案

**文档版本**: v1.0  
**创建日期**: 2026-05-14  
**对标对象**: [Zotero](https://www.zotero.org/) - 全球领先的开源文献管理工具  

---

## 一、Zotero 核心功能全景图

### 1.1 Zotero 产品定位

> **Your personal research assistant** - 个人研究助手

Zotero 是一款免费、开源的研究工具，帮助用户**收集、组织、引用和分享**研究成果。它不仅是文献管理器，更是完整的科研工作流平台。

### 1.2 Zotero 核心能力矩阵

| 维度 | 核心功能 | 技术实现 |
|------|---------|---------|
| **📥 采集** | 浏览器插件一键抓取网页文献元数据+PDF | Chrome/Firefox/Safari 扩展 |
| **🗂️ 组织** | 多级文件夹 + 标签系统 + 智能集合（Saved Searches） | 树形目录结构 |
| **📖 阅读** | 内置 PDF/EPUB 阅读器，支持高亮、批注、手写标注 | 原生 PDF 渲染引擎 |
| **✍️ 引用** | Word/WPS/LibreOffice/Google Docs 插件，10000+ 引用格式 | CSL (Citation Style Language) |
| **🔄 同步** | 跨设备云端同步（数据库+附件），支持 WebDAV 自建服务器 | 端到端加密同步 |
| **👥 协作** | 群组图书馆共享，实时协同批注 | Group Libraries |
| **🔌 生态** | 300+ 第三方插件（翻译、OCR、AI 摘要、思维导图等） | 开放 API + XUL 插件架构 |
| **📱 多端** | Windows/Mac/Linux/iOS/Android/Web 全平台覆盖 | 原生应用 + PWA |

---

## 二、PaperHub vs Zotero 功能对比

### 2.1 功能对标总览

| 功能模块 | Zotero | PaperHub | 差距分析 |
|---------|--------|----------|---------|
| **文献采集** | ⭐⭐⭐⭐⭐ 浏览器插件自动抓取 | ⭐⭐⭐ URL 手动导入 | 🔴 缺少浏览器插件 |
| **元数据提取** | ⭐⭐⭐⭐⭐ 自动识别 ISBN/DOI | ⭐⭐⭐ arXiv ID 解析 | 🟡 需增强通用网页元数据提取 |
| **PDF 阅读** | ⭐⭐⭐⭐⭐ 内置阅读器 + 批注 | ⭐⭐ 浏览器原生预览 | 🔴 缺少批注功能 |
| **引用生成** | ⭐⭐⭐⭐⭐ Word 插件 + 10000+ 格式 | ❌ 无此功能 | 🔴 完全缺失 |
| **全文检索** | ⭐⭐⭐⭐ FTS + 向量搜索 | ⭐⭐⭐ SQLite FTS5 | 🟢 基础能力已具备 |
| **标签系统** | ⭐⭐⭐⭐ 全局标签 + 自动标签 | ⭐⭐⭐ 三库独立标签 | 🟡 缺少全局标签视图 |
| **云同步** | ⭐⭐⭐⭐⭐ 官方云 + WebDAV | ❌ 纯本地存储 | 🔴 完全缺失 |
| **协作共享** | ⭐⭐⭐⭐⭐ 群组图书馆 | ❌ 单用户 | 🔴 完全缺失 |
| **插件生态** | ⭐⭐⭐⭐⭐ 300+ 插件 | ❌ 无插件系统 | 🔴 完全缺失 |
| **移动端** | ⭐⭐⭐⭐⭐ iOS/Android App | ❌ 仅 Web | 🔴 完全缺失 |
| **AI 集成** | ⭐⭐⭐ 社区插件（Zotero GPT） | ⭐⭐⭐⭐ 原生 AI 解读 | 🟢 PaperHub 领先 |
| **多源入库** | ⭐⭐⭐ 学术数据库为主 | ⭐⭐⭐⭐⭐ 论文/微信/知乎/网页 | 🟢 PaperHub 领先 |
| **笔记系统** | ⭐⭐⭐ 简单文本笔记 | ⭐⭐⭐⭐ Markdown + 图片粘贴 | 🟢 PaperHub 领先 |

### 2.2 PaperHub 优势领域

✅ **本土化内容支持**：微信公众号、知乎专栏深度适配  
✅ **AI 原生集成**：豆包/OpenAI/Claude 等多模型一键解读  
✅ **对话笔记沉淀**：大模型对话直接转知识库  
✅ **通用网页提取**：trafilatura/readability 多算法正文提取  
✅ **轻量级部署**：单文件前端 + Flask 后端，零配置启动  

### 2.3 PaperHub 明显短板

❌ **缺少浏览器插件**：无法实现"一键剪藏"  
❌ **PDF 阅读体验弱**：仅浏览器预览，无批注功能  
❌ **无引用管理**：无法在 Word 中插入参考文献  
❌ **无云同步**：数据仅限单机，存在丢失风险  
❌ **无协作能力**：不支持团队共享文献库  
❌ **无插件生态**：功能扩展依赖代码修改  
❌ **无移动端**：无法在手机/平板上阅读文献  

---

## 三、优化改进方向（按优先级排序）

### 🔴 P0 高优先级（建议 Phase 13-15 实施）

#### 1. 浏览器插件开发 - "一键剪藏"

**对标功能**：Zotero Connector（Chrome/Firefox/Safari）

**核心价值**：
- 用户在任意网页点击插件图标，自动提取标题、作者、摘要、发布时间
- 自动下载 PDF 附件并关联到条目
- 支持批量选择多个文献一次性入库

**技术方案**：
```
paperhub-extension/
├── manifest.json          # Chrome Extension V3
├── background.js          # 后台服务（监听右键菜单）
├── content.js             # 内容脚本（提取页面元数据）
├── popup.html             # 弹窗 UI（确认入库信息）
└── icons/                 # 插件图标
```

**关键 API**：
```javascript
// content.js - 提取网页元数据
function extractMetadata() {
    return {
        title: document.querySelector('meta[property="og:title"]')?.content,
        author: document.querySelector('meta[name="author"]')?.content,
        description: document.querySelector('meta[property="og:description"]')?.content,
        url: window.location.href,
        pdf_url: findPDFLinks() // 查找页面上的 PDF 链接
    };
}

// background.js - 发送到 PaperHub 后端
chrome.runtime.onMessage.addListener((request) => {
    fetch('http://localhost:5000/api/ingest/web', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request.metadata)
    });
});
```

**预期收益**：
- 文献采集效率提升 **10 倍**（从复制 URL → 点击一键入库）
- 用户体验对标 Zotero，降低学习成本

**预估工时**：3-5 天（含测试）

---

#### 2. PDF 阅读器升级 - 批注功能

**对标功能**：Zotero 内置 PDF 阅读器（高亮、下划线、批注、手写）

**核心价值**：
- 在 PaperHub 内直接阅读 PDF，无需跳转外部阅读器
- 支持高亮、下划线、文字批注、自由手绘
- 批注内容与原文位置永久绑定，可导出为 Markdown 报告

**技术方案**：
```python
# 方案 A：使用 PDF.js + 自定义批注层（推荐）
frontend/src/components/PDFReader.vue
├── PDF.js 渲染引擎
├── 批注图层（Canvas overlay）
├── 批注工具栏（高亮/下划线/批注/删除）
└── 批注侧边栏（显示所有批注列表）

# 方案 B：集成现有开源阅读器
# - react-pdf-highlighter
# - pdf-annotate.js
```

**数据存储**：
```sql
-- 新增批注表
CREATE TABLE annotations (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER NOT NULL,
    page_number INTEGER,           -- 页码
    annotation_type TEXT,          -- highlight/underline/note/drawing
    position JSON,                 -- {x, y, width, height}
    content TEXT,                  -- 批注文字内容
    color TEXT,                    -- 高亮颜色
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paper_id) REFERENCES papers(id) ON DELETE CASCADE
);
```

**预期收益**：
- 阅读体验从"被动浏览"升级为"主动标注"
- 批注可作为笔记素材，形成知识闭环

**预估工时**：5-7 天

---

#### 3. 数据备份与云同步

**对标功能**：Zotero Sync + WebDAV 自建服务器

**核心价值**：
- 防止数据丢失（硬盘损坏、误删）
- 多设备访问（家里/公司/实验室）
- 支持增量备份，节省存储空间

**技术方案**：
```python
# 方案 A：WebDAV 同步（推荐，兼容性好）
# services/sync_service.py
import webdav3.client as wc

class WebDAVSync:
    def __init__(self, url, username, password):
        self.client = wc.Client({
            'webdav_hostname': url,
            'webdav_login': username,
            'webdav_password': password
        })
    
    def upload_backup(self, backup_path):
        self.client.upload_dir(backup_path, '/paperhub_backups/')
    
    def download_backup(self, remote_path, local_path):
        self.client.download_dir(remote_path, local_path)

# 方案 B：iCloud/Dropbox 同步 data 目录
# 方案 C：自建 sync 服务（端到端加密）
```

**前端交互**：
```html
<!-- 设置页面新增同步配置 -->
<el-form label-width="120px">
    <el-form-item label="同步方式">
        <el-radio-group v-model="syncMethod">
            <el-radio label="webdav">WebDAV</el-radio>
            <el-radio label="icloud">iCloud</el-radio>
            <el-radio label="manual">手动备份</el-radio>
        </el-radio-group>
    </el-form-item>
    
    <template v-if="syncMethod === 'webdav'">
        <el-form-item label="WebDAV 地址">
            <el-input v-model="webdavUrl" placeholder="https://dav.example.com" />
        </el-form-item>
        <el-form-item label="用户名">
            <el-input v-model="webdavUser" />
        </el-form-item>
        <el-form-item label="密码">
            <el-input v-model="webdavPass" type="password" />
        </el-form-item>
        <el-button @click="testConnection">测试连接</el-button>
        <el-button @click="startSync" type="primary">开始同步</el-button>
    </template>
</el-form>
```

**预期收益**：
- 数据安全等级从"无保障"提升到"企业级"
- 支持多设备无缝切换工作场景

**预估工时**：2-3 天

---

### 🟡 P1 中优先级（建议 Phase 16-18 实施）

#### 4. 引用管理功能

**对标功能**：Zotero Word Plugin + CSL 引用样式

**核心价值**：
- 在 Word/WPS 中插入参考文献，自动生成书目
- 支持 APA/MLA/IEEE/GB/T 7714 等主流格式
- 一键切换引用风格

**技术方案**：
```python
# 方案 A：生成 BibTeX/RIS 文件（快速实现）
# api/citations.py
from pybtex.database import BibliographyData, Entry

def export_bibtex(paper_ids):
    bib = BibliographyData()
    for paper in get_papers_by_ids(paper_ids):
        entry = Entry('article', fields={
            'title': paper.title,
            'author': paper.author,
            'journal': paper.journal,
            'year': str(paper.year),
            'doi': paper.doi
        })
        bib.add_entry(f'paper_{paper.id}', entry)
    
    return bib.to_string('bibtex')

# 方案 B：Word 插件（长期目标）
# 需要开发 VSTO Add-in 或 Office JS API
```

**前端交互**：
```html
<!-- 论文列表页新增"导出引用"按钮 -->
<el-button @click="exportCitation(selectedPapers, 'bibtex')">
    导出 BibTeX
</el-button>
<el-button @click="exportCitation(selectedPapers, 'ris')">
    导出 RIS
</el-button>
<el-button @click="exportCitation(selectedPapers, 'gb7714')">
    导出 GB/T 7714
</el-button>
```

**预期收益**：
- 填补学术写作最后一环，形成完整工作流
- 吸引科研用户群体

**预估工时**：3-4 天（BibTeX/RIS 导出）；2-3 周（Word 插件）

---

#### 5. 全局标签视图

**对标功能**：Zotero 全局标签云 + 自动标签

**核心价值**：
- 跨论文/文章/笔记的统一标签视图
- 发现不同模块间的知识关联
- 智能推荐相关标签

**技术方案**：
```python
# api/tags.py
@app.route('/api/tags/global', methods=['GET'])
def get_global_tags():
    """获取全局标签统计"""
    tags = db.session.query(
        Tag.name,
        func.count(distinct(Paper.id)).label('paper_count'),
        func.count(distinct(Article.id)).label('article_count'),
        func.count(distinct(Note.id)).label('note_count')
    ).outerjoin(Paper.tags).outerjoin(Article.tags).outerjoin(Note.tags)\
     .group_by(Tag.name).all()
    
    return jsonify([{
        'name': tag.name,
        'paper_count': tag.paper_count,
        'article_count': tag.article_count,
        'note_count': tag.note_count,
        'total': tag.paper_count + tag.article_count + tag.note_count
    } for tag in tags])
```

**前端展示**：
```vue
<!-- 新增"全局标签"页面 -->
<template>
    <div class="global-tags-view">
        <h2>全局标签云</h2>
        <div class="tag-cloud">
            <el-tag 
                v-for="tag in sortedTags" 
                :key="tag.name"
                :size="getTagSize(tag.total)"
                @click="filterByTag(tag.name)"
            >
                {{ tag.name }} ({{ tag.total }})
            </el-tag>
        </div>
        
        <!-- 标签关联图谱（可选） -->
        <div class="tag-graph" ref="graphContainer"></div>
    </div>
</template>
```

**预期收益**：
- 打破三库隔离，发现跨领域知识关联
- 提升标签系统的战略价值

**预估工时**：1-2 天

---

#### 6. 智能集合（Saved Searches）

**对标功能**：Zotero Saved Searches（动态筛选条件保存）

**核心价值**：
- 保存常用筛选条件（如"最近 30 天的深度学习论文"）
- 自动更新结果，无需手动筛选
- 支持复杂组合条件（标签 + 状态 + 时间 + 关键词）

**技术方案**：
```sql
-- 新增智能集合表
CREATE TABLE saved_searches (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    conditions JSON NOT NULL,  -- {"tags": ["深度学习"], "date_range": "last_30_days", "status": "unread"}
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**前端交互**：
```vue
<!-- 侧边栏新增"智能集合"区域 -->
<div class="saved-searches">
    <h3>智能集合</h3>
    <el-button @click="showCreateDialog" size="small">+ 新建</el-button>
    
    <ul>
        <li v-for="search in savedSearches" :key="search.id">
            <span @click="applySearch(search.conditions)">
                {{ search.name }}
            </span>
            <el-button size="mini" @click="editSearch(search)">编辑</el-button>
        </li>
    </ul>
</div>
```

**预期收益**：
- 高频筛选操作从"每次手动选择"简化为"一键应用"
- 提升日常使用效率

**预估工时**：2-3 天

---

### 🟢 P2 长期规划（Phase 19+）

#### 7. 插件生态系统

**对标功能**：Zotero Plugins（300+ 社区插件）

**核心价值**：
- 开放 API，允许开发者扩展功能
- 社区驱动创新（翻译、OCR、AI 摘要、思维导图等）
- 形成生态壁垒

**技术方案**：
```python
# 设计插件架构
# plugins/manager.py
class PluginManager:
    def __init__(self):
        self.plugins = {}
    
    def load_plugin(self, plugin_path):
        """加载插件"""
        spec = importlib.util.spec_from_file_location("plugin", plugin_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # 注册插件钩子
        if hasattr(module, 'on_paper_import'):
            self.register_hook('on_paper_import', module.on_paper_import)
    
    def execute_hook(self, hook_name, *args, **kwargs):
        """执行钩子"""
        for callback in self.hooks.get(hook_name, []):
            callback(*args, **kwargs)

# 示例插件：PDF 翻译
# plugins/pdf_translate.py
def on_pdf_open(pdf_path):
    """PDF 打开时触发"""
    translate_pdf_to_chinese(pdf_path)
```

**预期收益**：
- 功能扩展不再依赖核心团队
- 形成活跃的开发者社区

**预估工时**：2-3 周（架构设计 + 文档）

---

#### 8. 移动端 App

**对标功能**：Zotero iOS/Android App

**核心价值**：
- 碎片时间阅读文献（通勤、排队）
- 离线缓存，无网络环境可用
- 触摸友好的批注体验

**技术方案**：
```
# 方案 A：Flutter 跨平台开发（推荐）
paperhub_mobile/
├── lib/
│   ├── screens/
│   │   ├── home_screen.dart
│   │   ├── pdf_reader_screen.dart
│   │   └── note_editor_screen.dart
│   ├── services/
│   │   ├── api_service.dart
│   │   └── sync_service.dart
│   └── models/
│       ├── paper.dart
│       └── note.dart
└── pubspec.yaml

# 方案 B：React Native
# 方案 C：PWA（渐进式 Web 应用，最快实现）
```

**预期收益**：
- 覆盖移动场景，提升用户使用频率
- 增强产品竞争力

**预估工时**：3-4 周（MVP 版本）

---

#### 9. 协作共享功能

**对标功能**：Zotero Group Libraries

**核心价值**：
- 团队共享文献库（课题组、实验室）
- 实时协同批注（多人同时标注同一篇论文）
- 权限管理（只读/读写/管理员）

**技术方案**：
```sql
-- 新增群组和权限表
CREATE TABLE groups (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    owner_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE group_members (
    group_id INTEGER,
    user_id INTEGER,
    role TEXT CHECK(role IN ('admin', 'editor', 'viewer')),
    PRIMARY KEY (group_id, user_id)
);

CREATE TABLE shared_annotations (
    id INTEGER PRIMARY KEY,
    paper_id INTEGER,
    user_id INTEGER,
    annotation_data JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**预期收益**：
- 切入团队协作市场，扩大用户群体
- 提升用户粘性（团队迁移成本高）

**预估工时**：2-3 周

---

## 四、实施路线图建议

### Phase 13-15（1-2 个月）- 补齐核心短板

| 任务 | 优先级 | 预计工时 | 关键里程碑 |
|------|--------|---------|-----------|
| 浏览器插件开发 | 🔴 P0 | 3-5 天 | Chrome 插件上架 |
| PDF 阅读器升级 | 🔴 P0 | 5-7 天 | 支持高亮/批注 |
| 数据备份与云同步 | 🔴 P0 | 2-3 天 | WebDAV 同步上线 |

**预期成果**：
- 文献采集效率提升 10 倍
- 阅读体验从"浏览"升级为"标注"
- 数据安全等级达到企业级

---

### Phase 16-18（2-3 个月）- 增强学术能力

| 任务 | 优先级 | 预计工时 | 关键里程碑 |
|------|--------|---------|-----------|
| 引用管理功能 | 🟡 P1 | 3-4 天 | BibTeX/RIS 导出 |
| 全局标签视图 | 🟡 P1 | 1-2 天 | 跨库标签云上线 |
| 智能集合 | 🟡 P1 | 2-3 天 | Saved Searches 功能 |

**预期成果**：
- 填补学术写作最后一环
- 发现跨领域知识关联
- 高频操作效率提升 50%

---

### Phase 19+（3-6 个月）- 生态建设

| 任务 | 优先级 | 预计工时 | 关键里程碑 |
|------|--------|---------|-----------|
| 插件生态系统 | 🟢 P2 | 2-3 周 | 插件 API 文档发布 |
| 移动端 App | 🟢 P2 | 3-4 周 | iOS/Android MVP |
| 协作共享功能 | 🟢 P2 | 2-3 周 | 群组图书馆上线 |

**预期成果**：
- 形成开发者社区
- 覆盖移动场景
- 切入团队协作市场

---

## 五、差异化竞争策略

### 5.1 PaperHub 的独特优势

| 维度 | Zotero | PaperHub | 策略 |
|------|--------|----------|------|
| **本土化** | 英文为主，中文支持弱 | 微信/知乎深度适配 | ✅ 强化本土内容生态 |
| **AI 集成** | 社区插件（非官方） | 原生多模型支持 | ✅ 深化 AI 解读能力 |
| **对话笔记** | 无此功能 | 大模型对话直接入库 | ✅ 打造"对话即知识"特色 |
| **部署难度** | 需安装客户端 + 插件 | 单文件启动，零配置 | ✅ 保持轻量级优势 |
| **网页提取** | 仅学术数据库 | trafilatura 通用提取 | ✅ 扩展非学术内容支持 |

### 5.2 避免正面竞争

❌ **不要做**：
- 完整的引用管理系统（Zotero 已有 10000+ 格式，追赶成本极高）
- 全平台原生应用（Zotero 团队 15 年积累，难以超越）
- 大型插件生态（需要多年社区运营）

✅ **应该做**：
- **AI 原生知识管理**：将 AI 解读、对话笔记作为核心卖点
- **本土内容专家**：深耕微信/知乎/B 站等中文平台
- **轻量级部署**：保持"开箱即用"优势，吸引非技术用户
- **垂直场景优化**：针对算法工程师、产品经理等特定群体定制功能

---

## 六、风险评估与应对

### 6.1 技术风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| PDF.js 性能问题 | 中 | 高 | 提前进行压力测试，优化渲染策略 |
| WebDAV 兼容性 | 低 | 中 | 提供多种同步方案（iCloud/Dropbox/手动） |
| 浏览器插件审核 | 中 | 低 | 提前准备隐私政策，遵循 Chrome Web Store 规范 |

### 6.2 产品风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| 功能过多导致复杂 | 高 | 高 | 坚持"一致性原则"，新功能必须复用现有交互模式 |
| 偏离核心用户群 | 中 | 中 | 每个新功能都要问："算法工程师会用吗？" |
| 维护成本激增 | 中 | 高 | 优先实现高 ROI 功能，避免过度工程化 |

### 6.3 市场风险

| 风险 | 概率 | 影响 | 应对措施 |
|------|------|------|---------|
| Zotero 推出类似功能 | 低 | 中 | 保持快速迭代，建立本土化壁垒 |
| 竞品出现（如 ReadCube） | 中 | 中 | 聚焦 AI + 本土内容差异化 |
| 用户需求变化 | 高 | 高 | 持续收集用户反馈，每月复盘功能使用率 |

---

## 七、成功指标定义

### 7.1 短期指标（3 个月）

| 指标 | 当前值 | 目标值 | 测量方式 |
|------|--------|--------|---------|
| 文献采集时间 | ~2 分钟/篇 | <20 秒/篇 | 用户行为日志 |
| PDF 批注使用率 | 0% | >30% | 功能使用统计 |
| 数据备份启用率 | 0% | >50% | 配置项统计 |

### 7.2 中期指标（6 个月）

| 指标 | 当前值 | 目标值 | 测量方式 |
|------|--------|--------|---------|
| 月活跃用户 | ~10 | ~100 | Google Analytics |
| 平均会话时长 | ~15 分钟 | ~30 分钟 | 会话统计 |
| 用户留存率（30 天） | ~40% | >60% |  Cohort 分析 |

### 7.3 长期指标（12 个月）

| 指标 | 当前值 | 目标值 | 测量方式 |
|------|--------|--------|---------|
| GitHub Stars | ~50 | >500 | GitHub API |
| 社区插件数量 | 0 | >10 | 插件市场统计 |
| 付费转化率 | 0% | >5% | 收入统计（如有商业化计划） |

---

## 八、总结与建议

### 8.1 核心结论

1. **PaperHub 已在 AI 集成和本土化方面建立优势**，应继续强化这两大差异化竞争力
2. **浏览器插件、PDF 批注、云同步是三大核心短板**，建议优先补齐
3. **避免与 Zotero 正面竞争引用管理和插件生态**，转而深耕垂直场景
4. **保持轻量级部署优势**，新功能不应显著增加使用复杂度

### 8.2 下一步行动

**立即执行（本周）**：
- [ ] 组建浏览器插件开发小组（1-2 人）
- [ ] 调研 PDF.js 批注方案，编写技术预研报告
- [ ] 设计 WebDAV 同步 API 接口规约

**短期计划（1 个月内）**：
- [ ] 完成浏览器插件 MVP 版本
- [ ] 实现 PDF 高亮/批注基础功能
- [ ] 上线数据备份/恢复功能（Phase 10 已完成，需增强为云同步）

**中期计划（3 个月内）**：
- [ ] 发布 Chrome/Firefox 插件正式版
- [ ] PDF 阅读器支持手写批注
- [ ] WebDAV/iCloud 同步稳定运行

### 8.3 最终愿景

> **成为算法工程师首选的 AI 原生知识管理平台**
> 
> 不是"另一个 Zotero"，而是"更懂中国研究者的智能助手"

---

*文档创建时间：2026-05-14*  
*下次复盘时间：2026-06-14（1 个月后评估进展）*
