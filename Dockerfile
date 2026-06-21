# ==========================================
# PaperHub Dockerfile
# 基于 Python 3.11 + Gunicorn 生产级部署
# ==========================================

FROM python:3.11-slim AS base

# 设置环境变量，避免 Python 生成 .pyc 文件、启用无缓冲输出
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TZ=Asia/Shanghai

# 安装系统依赖（lxml、PyMuPDF、trafilatura 等所需编译工具与运行时库）
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libxml2-dev \
        libxslt1-dev \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        libffi-dev \
        curl \
        ca-certificates \
        tzdata \
    && rm -rf /var/lib/apt/lists/* \
    && ln -snf /usr/share/zoneinfo/$TZ /etc/localtime \
    && echo $TZ > /etc/timezone

# 创建非 root 用户
RUN groupadd -r paperhub && useradd -r -g paperhub -m -d /home/paperhub -s /sbin/nologin paperhub

# 设置工作目录（必须命名为 PaperHub 以兼容 config.py 的 get_base_dir() 逻辑）
WORKDIR /app/PaperHub

# 先复制依赖清单，利用 Docker 缓存层加速构建
COPY backend/requirements-py11.txt ./backend/requirements-py11.txt

# 安装 Python 依赖 + gunicorn 生产 WSGI 服务器
RUN pip install --no-cache-dir -r backend/requirements-py11.txt \
    && pip install --no-cache-dir gunicorn==21.2.0

# 复制后端与前端代码
COPY backend/ ./backend/
COPY frontend/ ./frontend/

# 创建数据目录并赋权（数据卷挂载点）
RUN mkdir -p data/papers data/db data/backups data/vectors data/notes data/60s data/feishu_messages \
    && chown -R paperhub:paperhub /app/PaperHub

# 切换非 root 用户
USER paperhub

# 暴露端口（与 app.py 默认端口一致）
EXPOSE 5799

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -fsS http://localhost:5799/health || exit 1

# 使用 gunicorn 启动生产服务
# -w 4: 4 个 worker 进程（按 CPU 核数调整）
# -b: 绑定地址
# --timeout: 请求超时（PDF 上传/解析可能较慢，设为 120s）
# --access-logfile -: 输出访问日志到 stdout
CMD ["gunicorn", \
     "-w", "4", \
     "-b", "0.0.0.0:5799", \
     "--timeout", "120", \
     "--access-logfile", "-", \
     "--error-logfile", "-", \
     "backend.app:create_app('production')"]
