#  mind-generate MCP Server


---

##  项目简介

mind-generate MCP Server 是一款基于 Model Context Protocol (MCP) 的高性能思维导图自主化生成后端，适配 AI/自动化/智能助手等场景。界面友好，易于集成，开箱即用。

---

##  功能亮点

- 思维导图智能化一站式生成
- 支持资源提示词校验
- 内置可视化的思维导图页面，可进行编辑，放大缩小等操作
- Streamable HTTP传输协议，支持MCP 2025-08-26标准
- FastAPI异步高性能，秒级响应
- MCP标准，AI/自动化场景即插即用

---

## 架构图
![architecture.png](architecture.png)

## ️ 快速上手

### 环境要求
- Python 3.10+
- node 18+
- mindmap-cli 0.18.0
- [uv](https://astral.sh/uv/)（推荐包管理器）

### 本地一键部署
```bash
cd mcp-server-mcp-generate

# 安装依赖
uv sync

# 启动服务器
uv run python start_server.py
```

### Docker 部署
注意：本项目基础镜像为python311-node18-uv:latest，均已收录于 [`/base`](./base) 目录下，可按需打包编译
```bash
# 直接拉取已构建镜像
 docker pull cmss/mcp-server-mind-generate:latest

# 运行容器（映射8000端口）
 docker run -d -p 8000:8000 (-e XXX:XXX) --name mcp-server-mind-generate cmss/mcp-server-mind-generate:latest 
```

> 如需自定义开发或本地修改后再打包，可用如下命令自行构建镜像：
> ```bash
> docker build -t cmss/mcp-server-mind-generate:latest .
> ```

### 配置 (支持.env或docker或k8s环境变量)
1 复制 `.env.example` 为 `.env` 并按需修改：
```bash
cp .env.example .env

```
2 环境变量参考
以下是主要的环境变量配置：

环境变量	描述	默认值
SERVER_HOST	服务监听地址	0.0.0.0
SERVER_PORT	服务监听端口	8000
DEBUG	是否启用调试模式	false
LOG_LEVEL	日志级别	INFO
REQUEST_TIMEOUT	响应超时时间（秒）	30
HOST_URL  返回的主机ip 127.0.0.1
HOST_PORT  返回的主机端口 8000

---

### 健康检查
服务提供了/health端点用于健康检查，Kubernetes会定期调用该端点来监控服务状态。

---

## API & 工具一览

### MCP 客户端配置示例
```json
{
  "mcpServers": {
    "mind-generate": {
      "url": "http://localhost:8000/mcp"
    }
  }
}
```

### 支持的主流程工具
| 工具名                | 典型场景/功能描述       |
|--------------------|-----------------|
| generate_mind_html | 思维导图html图片一站式生成 |

---

## 工具文档

本项目所有主流程工具的详细功能、实现与使用方法，均已收录于 [`/docs`](./docs) 目录下：

- [generate_mind_html.md](./docs/generate_mind_html.md) — 思维导图html图片一站式生成


每个文档包含：
- 工具功能说明
- 实现方法
- 请求参数与返回示例
- 典型调用方式

如需二次开发或集成，建议先阅读对应工具的文档。

---

## 目录结构

```
src/mind-generate-mcp/    # 主源代码
  ├─ server.py    # FastAPI主入口
  ├─ models/      # 数据模型
  ├─ utils/       # 工具与配置
scripts/          # 启动与数据脚本
```

---

## 测试
```bash
uv run pytest
```

---

## 镜像发布与拉取

- 镜像仓库：[cmss/mcp-server-mcp-generate](https://{repo_url}/cmss/mcp-server-mcp-generate)
- 拉取镜像：
  ```bash
  docker pull cmss/mcp-server-mcp-generate:latest
  ```
- 运行镜像：
  ```bash
  docker run -d -p 8000:8000 --name mcp-generate-mcp-server cmss/mcp-server-mcp-generate:latest
  ```

---



