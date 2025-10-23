"""启动服务器脚本"""

import asyncio
from utils.custom_logger import logger
import sys
from importlib import import_module
from typing import List, Tuple
from utils.config import get_settings

settings = get_settings()
def check_environment() -> bool:
    """
    检查运行环境是否满足要求

    Returns:
        bool: 环境是否符合要求
    """
    logger.info("正在检查运行环境...")

    # 1. 检查 Python 版本
    if sys.version_info < (3, 10):
        logger.error(
            f"Python 版本过低: {'.'.join(map(str, sys.version_info[:3]))}，"
            f"当前需要 Python 3.10 或更高版本"
        )
        return False
    else:
        logger.info(f"Python 版本: {'.'.join(map(str, sys.version_info[:3]))}")

    # 2. 定义必要依赖包
    required_packages: List[Tuple[str, str]] = [
        ("mcp", "mcp-server"),
        ("fastapi", "fastapi"),
        ("httpx", "httpx"),
        ("pydantic", "pydantic>=2.0.0"),
        ("uvicorn", "uvicorn"),  # 可选但常见
    ]

    all_ok = True
    missing_packages = []

    logger.info("开始检查必要依赖...")

    for import_name, install_cmd in required_packages:
        try:
            import_module(import_name)
            logger.debug(f"{import_name} 已安装")
        except ImportError as e:
            logger.error(f"未找到包: {import_name}")
            missing_packages.append((import_name, install_cmd))
            all_ok = False

    if all_ok:
        logger.info("所有必要依赖已安装")
    else:
        logger.error("存在缺失的依赖包，请安装：")
        for _, install_cmd in missing_packages:
            logger.error(f"   pip install {install_cmd}")
        # 也可以提示 uv 或 poetry
        logger.error("提示: 如果使用 uv，可运行: uv pip install %s", " ".join(cmd for _, cmd in missing_packages))

    return all_ok


def main():
    """主函数"""
    mcp_type = settings.mcp_type
    try:
        # 环境检查
        if not check_environment():
            sys.exit(1)

        # 导入并运行服务器
        if mcp_type == "streamable-http":
            from server_mcp import main_server
        else:
            from server import main_server

        # 检查是否已有事件循环运行
        try:
            # 尝试获取当前事件循环
            loop = asyncio.get_running_loop()
            logger.info("检测到运行中的事件循环，使用当前循环")
            # 在当前循环中运行
            task = loop.create_task(main_server())
            loop.run_until_complete(task)
        except RuntimeError:
            # 没有运行中的事件循环，创建新的
            logger.info("创建新的事件循环")
            asyncio.run(main_server())

    except ImportError as e:
        logger.error(f"导入错误: {e}")
        logger.error("请确保已正确安装依赖: uv sync")
        sys.exit(1)
    except Exception as e:
        logger.error(f"启动失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
