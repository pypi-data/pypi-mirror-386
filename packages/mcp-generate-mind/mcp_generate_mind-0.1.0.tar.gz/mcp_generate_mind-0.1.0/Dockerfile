FROM python311-node18-uv:latest

# 安装 Supervisor
RUN apt-get update && apt-get install -y supervisor && apt-get install -y net-tools

# 设置工作目录。所有后续命令（如 COPY, RUN, CMD）都在这个目录下执行。
WORKDIR /app

# 将整个 FastAPI 项目代码复制到容器的工作目录。
COPY . .

# 创建虚拟环境
RUN uv venv

# uv 安装 Python 依赖。
RUN uv sync

# 创建 Supervisor 日志目录
RUN mkdir -p /app/log/ \
    && mkdir -p /app/run

# 暴露 FastAPI 应用将要监听的端口。
EXPOSE 8000

# 定义容器启动时执行的命令。
# --bind 0.0.0.0:8000 确保应用监听所有网络接口，以便从容器外部访问。
CMD ["bash","/app/start.sh"]
#CMD ["/usr/bin/supervisord", "-c", "/app/supervisord.conf --nodaemon"]
#CMD ["uv","run","python","./src/mcp-generate-mind/start_server.py"]

