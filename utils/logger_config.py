"""日志配置模块

配置项目级别的日志系统，统一管理日志输出。
"""
import logging
import sys
from pathlib import Path
from typing import Optional


def setup_logger(
    name: str,
    level: int = logging.INFO,
    log_file: Optional[Path] = None,
    console: bool = True
) -> logging.Logger:
    """设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别
        log_file: 日志文件路径（可选）
        console: 是否输出到控制台

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 清除已存在的处理器
    logger.handlers.clear()

    # 日志格式
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 控制台处理器
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    # 文件处理器
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(
            log_file,
            encoding='utf-8',
            mode='a'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger


# 预定义日志记录器
APP_LOGGER = setup_logger('OperationRecorder', level=logging.INFO)
VIDEO_LOGGER = setup_logger('VideoGenerator', level=logging.INFO)
WINDOW_LOGGER = setup_logger('WindowMonitor', level=logging.INFO)
EVENT_LOGGER = setup_logger('EventHandler', level=logging.INFO)
GUI_LOGGER = setup_logger('GUI', level=logging.INFO)
RECODER_LOGGER = setup_logger('RECODER_ENGINE', level=logging.INFO)


def get_logger(name: str) -> logging.Logger:
    """获取或创建日志记录器

    Args:
        name: 日志记录器名称

    Returns:
        logging.Logger: 日志记录器
    """
    return logging.getLogger(name)
