"""
通用日志配置模块
为 FastAPI 项目提供统一的日志输出：文件（DEBUG+）和控制台（INFO+）
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# === 日志文件路径配置 ===
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH",
                         os.path.join(os.path.dirname(os.path.dirname(__file__)), "sys.log"))
LOG_FILE_PATH = os.path.abspath(LOG_FILE_PATH)

# === 创建并配置 logger ===
logger = logging.getLogger("app")
logger.setLevel(logging.DEBUG)
logger.propagate = False

# 避免重复添加处理器
if not logger.handlers:
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 文件处理器：DEBUG+
    try:
        file_handler = RotatingFileHandler(
            LOG_FILE_PATH,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except (PermissionError, OSError) as e:
        print(f"【日志警告】无法创建日志文件 '{LOG_FILE_PATH}': {e}")

    # 控制台处理器：INFO+
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)