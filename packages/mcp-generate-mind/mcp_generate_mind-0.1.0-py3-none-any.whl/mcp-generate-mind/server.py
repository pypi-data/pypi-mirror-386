# -*- coding: utf-8 -*-
import asyncio
from datetime import datetime

import uvicorn
from mcp.server.fastmcp import FastMCP
from starlette.responses import FileResponse, JSONResponse, StreamingResponse
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.applications import Starlette
from starlette.routing import Mount, Host
from starlette.requests import Request
from starlette.routing import Route
import time
import subprocess
import os
import uuid
import html
from utils.config import get_settings
from utils.custom_logger import logger
from models.mind import Mind
from pathlib import Path

settings = get_settings()

MCP_PROTOCOL_VERSION = "2025-08-26"
SERVER_NAME = "generate-mind-mcp-server"
SERVER_VERSION = "1.0.0"

# Initialize FastMCP server
mcp = FastMCP(
    "mind-generate-mcp",
    host=settings.server_host,
    port=settings.server_port,
    instructions="基于MCP协议的思维导图生成服务"
)

MCP_TOOLS = [
    {
        "name": "generate_mind_html",
        "description": "处理Markdown上传并生成HTML思维导图，接收Markdown格式的文本内容，将其保存为文件，并返回上传结果信息，包括生成的文件名和访问路径",
        "inputSchema": {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "title": "Markdown格式的处理语句",
            "description": "生成HTML思维导图所需的参数",
            "properties": {
                "content": {"type": "string",
                            "title": "Markdown格式处理语句",
                            "description": "例如：# 标题\\n\\n这是内容",
                            "minLength": 1}
            },
            "required": ["content"],
            "additionalProperties": False
        }
    },
]

PROMPTS = {
    "markdown格式上下文": {
        "name": "markdown格式上下文",
        "title": "markdown格式上下文",
        "description": "以用户传入内容为主题，生成markdown格式的思维导图",
        "prompt": "生成markdown格式的思维导图",
        "messages": [
            {
                "role": "assistant",
                "content": """
                            角色：
                            你是一位思维导图生成大师，擅长将用户给定主题内容生成markdown格式的思维导图

                            任务：
                            1、根据用户给定主题内容生成markdown格式的思维导图
                            2. 保持专业术语的准确性

                            请按以下格式输出：
                            - 输出格式：仅markdown格式的思维导图，无其他文字内容
                            - 注意事项：确保逻辑结构清晰；内容合理；每层思维导图节点包含4-8个节点
                        """
            },
            {
                "role": "user",
                "content": """
                            角色：
                            你是一位思维导图生成大师，擅长将用户给定主题内容生成markdown格式的思维导图

                            任务：
                            1、根据用户给定主题内容生成markdown格式的思维导图
                            2. 保持专业术语的准确性

                            请按以下格式输出：
                            - 输出格式：仅markdown格式的思维导图，无其他文字内容
                            - 注意事项：确保逻辑结构清晰；内容合理；每层思维导图节点包含4-8个节点
                        """
            }
        ]
    }
    # 可扩展更多 prompt
}


async def root(request: Request):
    return {
        "name": "mind-generate MCP Server",
        "version": "1.0.0",
        "status": "running",
        "mcp_endpoint": "/mcp",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "Streamable HTTP (2025-03-26)",
        "tools": [tool["name"] for tool in MCP_TOOLS]
    }


async def health(request: Request):
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    }


async def get_tools_schema(request: Request):
    return {
        "tools": MCP_TOOLS,
        "schema_version": "http://json-schema.org/draft-07/schema#"
    }


async def sse_endpoint(request: Request):
    async def event_generator():
        while True:
            await asyncio.sleep(30)
            yield f"data: ping {datetime.now().isoformat()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


@mcp.prompt()
async def list_prompts():
    return PROMPTS


#  >>> 此工具接收 Markdown 格式的文本内容，将其保存为文件，并返回上传结果信息，包括生成的文件名和访问路径。<<<
"""
###处理 Markdown 上传并生成 HTML 思维导图。
    >>> 此工具接收 Markdown 格式的文本内容，将其保存为文件，并返回上传结果信息，包括生成的文件名和访问路径。

###输入参数:
    >>> content：包含Markdown格式的文本内容

###输出参数:
    >>> return：包含生成的思维导图的HTML访问路径

####示例:
    >>> 请求 = content="# 标题\\n\\n这是内容",
    >>> 返回 = "http://127.0.0.1:8000/html/XXXX.html"
"""
@mcp.tool()
async def generate_mind_html(content: str) -> str:
    """
    处理Markdown上传并生成HTML思维导图，接收Markdown格式的文本内容，将其保存为文件，并返回上传结果信息，包括生成的文件名和访问路径
    """
    if not content:
        raise HTTPException(status_code=400, detail="JSON 数据中缺少 'content' 字段")

    # 将content中<>进行转义，防止出现html中存在注入情况，主要转义: &, <, >, ", '
    content = html.escape(content)
    # 此时 content 中的 '<' 变成 '&lt;', '>' 变成 '&gt;' 等，不会再被浏览器解析为标签
    logger.debug(f"转义后的 content: {content}")

    # 生成唯一文件名
    time_name = str(int(time.time())) + "_" + str(uuid.uuid4())[:8]
    file_name = f"{time_name}.md"
    html_name = f"{time_name}.html"
    # 动态环境变量获取
    host_url = settings.host_url
    host_port = settings.host_port
    timeout = settings.request_timeout

    # 保存Markdown文件
    file_path = f"markdown/{file_name}"
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    except Exception as e:
        logger.error(f"保存Markdown文件时出错: {str(e)}")
        raise HTTPException(status_code=500, detail=f"保存Markdown文件时出错: {str(e)}")

    # 转换md为html
    try:
        result = subprocess.run(
            ['markmap', file_path, '--no-open', '-o', f'markdown/{html_name}'],
            capture_output=True,
            text=True,
            timeout=timeout  # 设置超时时间
        )

        if result.returncode != 0:
            logger.error(f"生成HTML失败: {result.stderr}")
            return f"生成HTML失败: {result.stderr}"

    except subprocess.TimeoutExpired:
        logger.error("生成HTML超时")
        return "生成HTML超时"
    except Exception as e:
        msg = f"生成HTML时出错: {str(e)}"
        logger.error(msg)
        return msg

    logger.info(
        f"Markdown 文件 {file_name} 已保存并转换为 HTML {html_name}, 预览地址: http://{host_url}:{host_port}/html/{html_name}")
    return f"http://{host_url}:{host_port}/html/{html_name}"


# 该接口返回思维导图连接的html文件内容
async def query_mind_html(request: Request) -> FileResponse | JSONResponse:
    filename = request.path_params.get("filename")
    # 安全检查：确保请求的是HTML文件且路径在markdown目录内
    if not filename.endswith('.html') or '/' in filename or '\\' in filename:
        return JSONResponse(status_code=400, content={"detail": "无效的文件名"})

    file_path = f"markdown/{filename}"
    logger.info(f"请求HTML文件: {file_path}")

    if not os.path.exists(file_path):
        return JSONResponse(status_code=404, content={"detail": "文件未找到"})

    return FileResponse(file_path, media_type="text/html")


# ----------------------------------------------------------------------
# 动态构建 Starlette APP 和主启动逻辑
# ----------------------------------------------------------------------

def create_app(mcp_transport: str):
    """根据传输类型创建 Starlette 应用并挂载 FastMCP 应用。"""

    mcp_app = mcp.sse_app()

    # 基础路由（非 MCP 路由）
    routes = [
        Route("/root", endpoint=root, methods=["GET"]),
        Route("/health", endpoint=health, methods=["GET"]),
        Route("/schema/tools", endpoint=get_tools_schema, methods=["GET"]),
        Route("/html/{filename}", endpoint=query_mind_html, methods=["GET"]),
    ]

    # 挂载 MCP App
    if mcp_app:
        routes.append(Mount("/", app=mcp_app))

    app = Starlette(routes=routes)

    # CORS 中间件
    app = CORSMiddleware(
        app,
        allow_origins=settings.allow_origins,
        allow_credentials=True,
        allow_methods=settings.allow_methods,
        allow_headers=settings.allow_headers,
        expose_headers=["*"],
    )

    return app


async def main_server():
    mcp_type = settings.mcp_type

    """启动MCP服务器"""
    logger.info("启动思维导图生成MCP服务器...")
    logger.info(f"协议版本: {MCP_PROTOCOL_VERSION}")
    logger.info(f"配置传输类型: {mcp_type}")
    logger.info(f"健康检查: http://{settings.server_host}:{settings.server_port}/health")

    # 1. 确保目录存在
    Path("markdown").mkdir(exist_ok=True)

    # 2. 特殊处理 stdio 模式（不需要 uvicorn）
    if mcp_type == "stdio":
        logger.info("STDIO 模式启动。将直接调用 mcp.run()，不启动 Uvicorn。")
        try:
            mcp.run(transport="stdio")
        except Exception as e:
            logger.error(f"STDIO server failed: {e}")
        return

    elif mcp_type == "sse":

        # 3. 创建 Starlette 应用（动态挂载 MCP 传输）
        final_app = create_app(mcp_type)

        # 4. 配置并启动 Uvicorn 服务器
        config = uvicorn.Config(
            final_app,
            host=settings.server_host,
            port=settings.server_port,
            log_level=settings.log_level.lower(),
            # 重要的异步启动配置
            loop="auto",
            reload=settings.debug  # 假设 settings.debug 控制是否热重载
        )

        uvicorn_server = uvicorn.Server(config)
        # 使用 await uvicorn_server.serve() 替代 uvicorn.run() 以便在 asyncio.run 中优雅启动
        await uvicorn_server.serve()


def main():
    # 使用 asyncio.run 启动异步主函数
    try:
        asyncio.run(main_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"An error occurred during server startup: {e}")


if __name__ == "__main__":
    main()
