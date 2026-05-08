# PaperHub - 数据库 Schema

---

## 分类预设

### 一级分类 (category_l1)
- 大模型
- 计算机视觉
- Agent
- 多模态
- 工程落地

### 二级分类 (category_l2)

| 一级分类 | 二级分类 |
|---------|---------|
| 大模型 | 预训练、对齐、推理优化、模型压缩 |
| 计算机视觉 | 目标检测、图像分割、OCR、多模态 |
| Agent | 架构设计、工具调用、Memory机制 |
| 多模态 | 图文预训练、视频理解、跨模态检索 |
| 工程落地 | 部署优化、MLOps、量化蒸馏 |

---

## 阅读状态 (status)
- `pending` - 待读
- `reading` - 在读
- `done` - 已读
- `mastered` - 精读

---

## 标签类型 (tag.type)
- `tech` - 技术标签 (Transformer, YOLO, RAG...)
- `conference` - 会议标签 (CVPR2024, NeurIPS...)
- `custom` - 自定义标签 (必读, 待复现...)

---

## 数据表定义

### 1. papers 表
论文/文章主表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| title | TEXT | NOT NULL | 标题 |
| authors | TEXT | | JSON 数组格式存储 |
| abstract | TEXT | | 摘要 |
| content | TEXT | | 全文内容 |
| url | TEXT | | 原文链接 |
| source | TEXT | NOT NULL | 来源: arxiv/wechat/blog/conference |
| doi | TEXT | | DOI |
| arxiv_id | TEXT | | arXiv ID (如 2310.06825) |
| published_at | DATE | | 发表时间 |
| category_l1 | TEXT | | 一级分类 |
| category_l2 | TEXT | | 二级分类 |
| file_path | TEXT | | PDF本地路径 |
| status | TEXT | DEFAULT 'pending' | 阅读状态 |
| starred | BOOLEAN | DEFAULT 0 | 是否标星 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- `idx_papers_title` - 标题索引
- `idx_papers_category` - 分类索引
- `idx_papers_status` - 状态索引
- `idx_papers_starred` - 标星索引
- `idx_papers_published` - 发表时间索引
- `idx_papers_arxiv_id` - arXiv ID 索引

---

### 2. tags 表
标签表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| name | TEXT | NOT NULL UNIQUE | 标签名称 |
| type | TEXT | NOT NULL DEFAULT 'custom' | 标签类型: tech/conference/custom |
| color | TEXT | | 标签颜色 (十六进制, 如 #409EFF) |
| parent_id | INTEGER | | 父标签ID (支持层级) |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**索引**:
- `idx_tags_type` - 类型索引
- `idx_tags_parent` - 父标签索引

---

### 3. paper_tags 表
论文-标签关联表 (多对多)

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| paper_id | INTEGER | NOT NULL REFERENCES papers(id) | 论文ID |
| tag_id | INTEGER | NOT NULL REFERENCES tags(id) | 标签ID |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

**主键**: `(paper_id, tag_id)`

---

### 4. notes 表
笔记/批注表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| paper_id | INTEGER | NOT NULL REFERENCES papers(id) | 论文ID |
| content | TEXT | NOT NULL | 笔记内容 |
| page_num | INTEGER | | 页码 |
| highlight_rect | TEXT | | JSON格式的高亮区域坐标 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 更新时间 |

**索引**:
- `idx_notes_paper` - 论文ID索引

---

### 5. paper_versions 表
论文版本管理表

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| id | INTEGER | PRIMARY KEY | 主键 |
| paper_id | INTEGER | NOT NULL REFERENCES papers(id) | 论文ID |
| version | TEXT | NOT NULL | 版本号 (v1, v2...) |
| file_path | TEXT | NOT NULL | PDF文件路径 |
| diff_summary | TEXT | | 版本差异摘要 |
| created_at | TIMESTAMP | DEFAULT CURRENT_TIMESTAMP | 创建时间 |

---

## SQLite FTS5 全文检索

创建虚拟表用于全文检索:

```sql
CREATE VIRTUAL TABLE papers_fts USING fts5(
    title,
    abstract,
    content,
    authors,
    content=papers,
    content_rowid=id
);
```

---

## 初始化数据

### 预设标签

**技术标签**:
- Transformer
- Diffusion
- YOLO
- RAG
- LoRA
- LLM
- CNN
- ViT

**会议标签**:
- CVPR2024
- ICCV2023
- NeurIPS2024
- ICML2024
- arXiv

**自定义标签**:
- 必读
- 待复现
- 落地可用
- 冷门但有启发
