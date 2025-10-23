# 使用 Node.js 18 官方镜像（基于 Debian 12/bookworm）
FROM node:18-bookworm

# 设置非交互模式
ENV DEBIAN_FRONTEND=noninteractive

# 安装 Python 3 和常用工具
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        python3-dev \
        vim \
        curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# 创建软链接，方便使用 python3 -> python
RUN ln -sf python3 /usr/bin/python && \
    ln -sf pip3 /usr/local/bin/pip
# 创建虚拟环境
RUN python -m venv /opt/venv

# 设置环境变量，激活虚拟环境
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 下载并安装 uv（使用官方安装脚本）
RUN curl -LsSf https://astral.sh/uv/install.sh | sh

# 将 uv 添加到 PATH
ENV PATH="/root/.local/bin:${PATH}"

# 验证安装
RUN uv --version

# 升级 pip
RUN uv pip install --no-cache-dir --upgrade pip

# 安装 Python 包到虚拟环境中
RUN uv pip install flask uvicorn fastapi

# 可选：设置工作目录
WORKDIR /app

RUN npm install -g markmap-cli --registry=https://registry.npmmirror.com

