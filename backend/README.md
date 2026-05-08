# PaperHub Backend

---

## ⚠️ Python 解释器配置

**必须使用**: `/opt/anaconda3/envs/py38/bin/python`

> 所有 Python 命令都必须使用此解释器，不要使用系统默认的 python3

### 验证方法

```bash
/opt/anaconda3/envs/py38/bin/python --version
# 输出应该是 Python 3.8.x
```

### 快速启动

**macOS/Linux**:
```bash
cd backend
./start.sh
```

**Windows**:
```batch
cd backend
start.bat
```

### 手动启动

```bash
cd backend
/opt/anaconda3/envs/py38/bin/python app.py 5799
```

启动后访问: **http://localhost:5799**

---

## 目录结构

```
backend/
├── app.py              # Flask 主应用
├── config.py           # 配置文件
├── requirements.txt    # Python 依赖
├── start.sh           # Linux/macOS 启动脚本
├── start.bat          # Windows 启动脚本
├── api/               # API 路由
│   ├── papers.py      # 论文 CRUD
│   ├── articles.py    # 文章库 API
│   ├── notes.py       # 笔记库 API
│   ├── ingest.py      # 统一入库接口
│   └── ai.py          # AI 解读 API
├── services/          # 业务逻辑
│   ├── arxiv_fetcher.py
│   ├── pdf_processor.py
│   ├── llm_client.py  # 大模型客户端
│   └── deduplicator.py
└── models/            # 数据模型
```

---

## 依赖安装

```bash
/opt/anaconda3/envs/py38/bin/python -m pip install -r requirements.txt
```

---

*文档更新：2026-05-05*
