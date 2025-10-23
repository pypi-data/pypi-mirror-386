import asyncio
import json
import os
import html
import subprocess
import time
from datetime import datetime
from typing import Dict
import uuid

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse, JSONResponse, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import uvicorn
from pathlib import Path

from models.mind import Mind
from utils.config import get_settings
from utils.custom_logger import logger

settings = get_settings()

# MCP Protocol Version - Support 2025-08-26 Streamable HTTP transport
MCP_PROTOCOL_VERSION = "2025-08-26"
SERVER_NAME = "generate-mind-mcp-server"
SERVER_VERSION = "1.0.0"

USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/123.0.0.0 Safari/537.36"
)

# Connected clients for session management
connected_clients: Dict[str, Dict] = {}

# MCP Tools Definition according to spec
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

app = FastAPI(
    title="mind-generate MCP Server",
    version="1.0.0",
    description="基于MCP协议(2025-08-26 Streamable HTTP)的思维导图生成服务",
    debug=settings.debug
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def root():
    return {
        "name": "mind-generate MCP Server",
        "version": "1.0.0",
        "status": "running",
        "mcp_endpoint": "/mcp",
        "protocol_version": MCP_PROTOCOL_VERSION,
        "transport": "Streamable HTTP (2025-03-26)",
        "tools": [tool["name"] for tool in MCP_TOOLS],
        "active_sessions": len(connected_clients)
    }


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "active_sessions": len(connected_clients)
    }


@app.get("/schema/tools")
async def get_tools_schema():
    return {
        "tools": MCP_TOOLS,
        "schema_version": "http://json-schema.org/draft-07/schema#"
    }


# MCP Streamable HTTP Transport Endpoints (2025-03-26 spec)

@app.options("/mcp")
async def mcp_options():
    """Handle CORS preflight for /mcp endpoint"""
    return JSONResponse(
        {},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, Mcp-Session-Id",
        }
    )


@app.get("/mcp")
async def mcp_endpoint_get(request: Request):
    """MCP Streamable HTTP Endpoint - GET for SSE connection (optional)"""
    # Generate session ID for this connection
    session_id = str(uuid.uuid4())
    logger.info(f"🔗 New MCP GET connection established - Session ID: {session_id}")

    # Store client connection info
    connected_clients[session_id] = {
        "connected_at": datetime.now().isoformat(),
        "user_agent": request.headers.get("user-agent", ""),
        "client_ip": request.client.host if request.client else "unknown",
        "initialized": False,
        "protocol_version": MCP_PROTOCOL_VERSION
    }

    async def generate_events():
        try:
            # Keep connection alive with periodic pings
            while True:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                yield f"event: ping\ndata: {{\"timestamp\": \"{datetime.now().isoformat()}\"}}\n\n"

        except asyncio.CancelledError:
            logger.info(f"MCP GET connection closed - Session ID: {session_id}")
            # Clean up client connection
            if session_id in connected_clients:
                del connected_clients[session_id]
        except Exception as e:
            logger.error(f"MCP GET error for session {session_id}: {e}")
            # Clean up client connection
            if session_id in connected_clients:
                del connected_clients[session_id]

    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "*",
            "X-Accel-Buffering": "no",  # Disable nginx buffering
            "Mcp-Session-Id": session_id  # Return session ID in header
        }
    )


@app.post("/mcp")
async def mcp_endpoint_post(request: Request):
    """MCP Streamable HTTP Endpoint - POST for JSON-RPC messages"""
    request_id = None
    try:
        data = await request.json()

        # Validate JSON-RPC 2.0 format
        if not isinstance(data, dict) or data.get("jsonrpc") != "2.0":
            raise HTTPException(status_code=400, detail="Invalid JSON-RPC 2.0 message")

        method = data.get("method")
        params = data.get("params", {})
        request_id = data.get("id")

        if not method:
            raise HTTPException(status_code=400, detail="Method is required")

        logger.info(f"Received MCP request: {method} (ID: {request_id})")

        # Handle initialization - no session ID required for this
        if method == "initialize":
            client_capabilities = params.get("capabilities", {})
            client_protocol_version = params.get("protocolVersion", MCP_PROTOCOL_VERSION)
            client_info = params.get("clientInfo", {})

            logger.info(f"Initialize request - Client Protocol: {client_protocol_version}")
            logger.info(f"Client Info: {client_info}")

            # Generate new session ID for this client
            session_id = str(uuid.uuid4())

            # Store session info
            connected_clients[session_id] = {
                "connected_at": datetime.now().isoformat(),
                "user_agent": request.headers.get("user-agent", ""),
                "client_ip": request.client.host if request.client else "unknown",
                "initialized": False,
                "protocol_version": client_protocol_version
            }

            # Accept the client's protocol version or use our default
            accepted_version = client_protocol_version if client_protocol_version else MCP_PROTOCOL_VERSION

            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": accepted_version,
                    "serverInfo": {
                        "name": SERVER_NAME,
                        "version": SERVER_VERSION,
                        "description": "支持Markdown格式内容处理，生成思维导图服务"
                    },
                    "capabilities": {
                        "tools": {},  # Server supports tools
                        "logging": {}  # Server supports logging
                    }
                }
            }

            # Return response with Mcp-Session-Id header
            logger.info(f"Initialize response sent - Protocol: {accepted_version}, Session: {session_id}")
            return JSONResponse(
                response,
                headers={
                    "Mcp-Session-Id": session_id,
                    "Access-Control-Allow-Origin": "*"
                }
            )

        # For all other methods, require session ID
        session_id = request.headers.get("mcp-session-id")
        if not session_id:
            logger.error("Missing Mcp-Session-Id header for non-initialize request")
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": "Bad Request: No valid session ID provided"
                    }
                },
                status_code=400
            )

        # Validate session exists
        if session_id not in connected_clients:
            logger.error(f"Invalid session ID: {session_id}")
            return JSONResponse(
                {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32000,
                        "message": "Invalid session ID"
                    }
                },
                status_code=404  # Use 404 for invalid session as per spec
            )

        logger.info(f"Processing message for session: {session_id}")

        # Handle tool listing
        if method == "tools/list":
            logger.info("Tools list requested")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": MCP_TOOLS
                }
            }
            return JSONResponse(response)
        # 新增 prompts/list 支持
        elif method == "prompts/list":
            logger.info("Prompts list requested")
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "prompts": list(PROMPTS.values())
                }
            }
            return JSONResponse(response)
        # Handle tool execution
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})

            if not tool_name:
                raise HTTPException(status_code=400, detail="Tool name is required")

            logger.info(f"Executing tool: {tool_name}")
            logger.info(f"Arguments: {arguments}")

            # Execute the appropriate tool
            try:
                # Map tool names with hyphens to underscores for internal functions
                if tool_name == "generate_mind_html":

                    content = await generate_mind_html(Mind(content=arguments.get("content")))
                else:
                    content = [{
                        "type": "text",
                        "text": f"未知工具: {tool_name}"
                    }]

                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": content,
                        "isError": False
                    }
                }
                logger.info(f"Tool {tool_name} executed successfully")

            except Exception as tool_error:
                logger.error(f"Tool execution error: {tool_error}")
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "result": {
                        "content": [{
                            "type": "text",
                            "text": f"工具执行失败: {str(tool_error)}"
                        }],
                        "isError": True
                    }
                }

            return JSONResponse(response)

        # Handle notifications (no response required)
        elif method and method.startswith("notifications/"):
            notification_type = method.replace("notifications/", "")
            logger.info(f"Received notification: {notification_type}")

            # Process notification but don't send response
            if notification_type == "initialized":
                logger.info("Client initialized successfully - MCP handshake complete!")
                # Mark session as fully initialized
                if session_id in connected_clients:
                    connected_clients[session_id]["initialized"] = True

            # Notifications should return 202 Accepted according to MCP spec
            return Response(status_code=202)  # Accepted

        # Handle ping requests
        elif method == "ping":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "timestamp": datetime.now().isoformat(),
                    "status": "alive"
                }
            }
            return JSONResponse(response)

        # Unknown method
        else:
            logger.warning(f"Unknown method: {method}")
            error_response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": "Method not found",
                    "data": {"method": method}
                }
            }
            return JSONResponse(error_response, status_code=404)

    except json.JSONDecodeError:
        logger.error("Invalid JSON in request")
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": None,
                "error": {
                    "code": -32700,
                    "message": "Parse error"
                }
            },
            status_code=400
        )
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return JSONResponse(
            {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32603,
                    "message": "Internal error",
                    "data": {"error": str(e)}
                }
            },
            status_code=500
        )


#  >>> 此工具接收 Markdown 格式的文本内容，将其保存为文件，并返回上传结果信息，包括生成的文件名和访问路径。<<<
async def generate_mind_html(args: Mind) -> list:

    content = args.content
    logger.info(f"接收到新的Markdown内容, content: {content}")
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
            return [{"type": "text", "text": f"生成HTML失败: {result.stderr}"}]

    except subprocess.TimeoutExpired:
        logger.error("生成HTML超时")
        return [{"type": "text", "text": "生成HTML超时"}]
    except Exception as e:
        msg = f"生成HTML时出错: {str(e)}"
        logger.error(msg)
        return [{"type": "text", "text": msg}]

    logger.info(
        f"Markdown 文件 {file_name} 已保存并转换为 HTML {html_name}, 预览地址: http://{host_url}:{host_port}/html/{html_name}")
    url = f"http://{host_url}:{host_port}/html/{html_name}"
    return [{"type": "text", "text": url}]


# 该接口返回思维导图连接的html文件内容
@app.get("/html/{filename}")
async def query_mind_html(filename: str) -> FileResponse:
    # 安全检查：确保请求的是HTML文件且路径在markdown目录内
    if not filename.endswith('.html') or '/' in filename or '\\' in filename:
        raise HTTPException(status_code=400, detail="无效的文件名")

    file_path = f"markdown/{filename}"

    logger.info(f"请求HTML文件: {file_path}")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="文件未找到")

    return FileResponse(file_path, media_type="text/html")


@app.delete("/mcp")
async def mcp_endpoint_delete(request: Request):
    """MCP Streamable HTTP Endpoint - DELETE for session termination"""
    session_id = request.headers.get("mcp-session-id")

    if not session_id:
        return JSONResponse(
            {"error": "Missing Mcp-Session-Id header"},
            status_code=400
        )

    if session_id in connected_clients:
        del connected_clients[session_id]
        logger.info(f"🗑️ Session terminated: {session_id}")
        return Response(status_code=200)
    else:
        return JSONResponse(
            {"error": "Invalid session ID"},
            status_code=404
        )


# 新增 /sse 路由，兼容部分客户端
@app.get("/sse")
async def sse_endpoint():
    async def event_generator():
        while True:
            await asyncio.sleep(30)
            yield f"data: ping {datetime.now().isoformat()}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")


async def main_server():
    """启动MCP服务器"""
    logger.info("启动思维导图生成MCP服务器....")
    logger.info(f"协议版本: {MCP_PROTOCOL_VERSION}")
    logger.info(f"配置传输类型: Stream HTTP")
    logger.info(f"健康检查: http://{settings.server_host}:{settings.server_port}/health")

    # 1. 确保目录存在
    Path("markdown").mkdir(exist_ok=True)

    config = uvicorn.Config(
        app,
        host=settings.server_host,
        port=settings.server_port,
        log_level=settings.log_level.lower()
    )
    uvicorn_server = uvicorn.Server(config)
    await uvicorn_server.serve()


def main():
    asyncio.run(main_server())


if __name__ == "__main__":
    main()
