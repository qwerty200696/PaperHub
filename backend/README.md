# PaperHub Backend

---

## ⚠️ Python 解释器配置

**推荐使用**: `python3`

> 所有 Python 命令都应使用 python3，不要使用系统默认的 python
>
> **注意**: 如果使用 conda 环境，请在环境中创建软链接:
> ```bash
> ln -s /opt/anaconda3/envs/py38/bin/python python3
> # 或者将 conda 环境的 bin 目录添加到 PATH
> export PATH="/opt/anaconda3/envs/py38/bin:$PATH"
> ```

### 验证方法

```bash
python3 --version
# 输出应该是 Python 3.8.x 或更高版本
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
python3 app.py 5799
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
python3 -m pip install -r requirements.txt
```

---

*文档更新：2026-05-05*
