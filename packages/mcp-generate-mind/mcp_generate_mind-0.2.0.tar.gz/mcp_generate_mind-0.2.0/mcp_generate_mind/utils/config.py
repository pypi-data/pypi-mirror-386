"""配置管理 - 支持 .env 文件和环境变量（环境变量优先）"""

from typing import Optional
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from .custom_logger import logger

# 定义 .env 文件路径（可自定义）
ENV_FILE_PATH = Path(__file__).parent.parent / ".env"


class Settings(BaseSettings):
    """应用配置：支持 .env 文件 + 环境变量（环境变量优先级更高）"""

    server_host: str = Field(
        default="0.0.0.0",
        description="服务器主机地址",
        alias="SERVER_HOST",
    )
    server_port: int = Field(
        default=8000,
        description="服务器端口",
        alias="SERVER_PORT",
    )
    debug: bool = Field(
        default=False,
        description="调试模式",
        alias="DEBUG",
    )
    user_agent: str = Field(
        default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="用户代理字符串",
        alias="USER_AGENT",
    )
    request_timeout: int = Field(
        default=300,
        description="请求超时时间（秒）",
        alias="REQUEST_TIMEOUT",
    )
    log_level: str = Field(
        default="INFO",
        description="日志级别",
        alias="LOG_LEVEL",
    )
    host_url: str = Field(
        default="127.0.0.1",
        description="返回的主机ip",
        alias="HOST_URL",
    )
    host_port: int = Field(
        default=8000,
        description="返回的主机端口",
        alias="HOST_PORT",
    )
    mcp_type: str = Field(
        default="streamable-http",
        description="mcp传输类型：stdio/sse/streamable-http",
        alias="MCP_TYPE",
    )
    allow_origins: list = Field(
        default=["*"],
        description="允许来源",
        alias="ALLOW_ORIGINS",
    )
    allow_methods: list = Field(
        default=["*"],
        description="允许方法",
        alias="ALLOW_METHODS",
    )
    allow_headers: list = Field(
        default=["*"],
        description="允许请求头",
        alias="ALLOW_HEADERS",
    )

    # 关键配置：启用 .env 文件，并设置优先级
    model_config = SettingsConfigDict(
        env_file=ENV_FILE_PATH,      # 启用 .env 文件
        env_file_encoding="utf-8",   # 支持中文
        extra="ignore",              # 忽略多余字段
        case_sensitive=False,        # 不区分大小写
    )


_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    获取配置实例（单例模式）

    优先级：环境变量 > .env 文件 > 默认值
    """
    global _settings
    if _settings is None:
        # 日志提示配置加载开始
        if ENV_FILE_PATH.exists():
            logger.info(f"加载配置文件: {ENV_FILE_PATH.absolute()}")
        else:
            logger.warning(f"⚠配置文件未找到: {ENV_FILE_PATH.absolute()}，将尝试从环境变量加载")

        try:
            _settings = Settings()
        except Exception as e:
            logger.error(f"配置加载发生未知错误: {type(e).__name__}: {e}，使用默认值")
            _settings = Settings.model_construct()

    return _settings