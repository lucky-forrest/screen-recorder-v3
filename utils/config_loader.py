"""配置加载器

加载和管理程序配置文件。
"""
from typing import Any, Dict
import json
import os
from pathlib import Path


def load_config(config_path: str = "config.json") -> Dict[str, Any]:
    """加载配置文件

    Args:
        config_path: 配置文件路径

    Returns:
        Dict[str, Any]: 配置字典
    """
    if not os.path.exists(config_path):
        return _get_default_config()

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)
        # 确保output目录结构存在
        _ensure_output_dirs(config)
        return config
    except Exception as e:
        print(f"Error loading config: {e}, using defaults")
        return _get_default_config()


def _ensure_output_dirs(config: Dict[str, Any]):
    """确保输出目录结构存在

    Args:
        config: 配置字典
    """
    # 检查是否有output配置
    if "output" in config:
        output_config = config["output"]

        # 创建主output目录
        main_dir = output_config.get("path")
        if main_dir:
            Path(main_dir).mkdir(parents=True, exist_ok=True)

        # 创建data子目录
        data_dir = output_config.get("data")
        if data_dir:
            Path(data_dir).mkdir(parents=True, exist_ok=True)

        # 创建videos子目录
        videos_dir = output_config.get("videos")
        if videos_dir:
            Path(videos_dir).mkdir(parents=True, exist_ok=True)


def _get_default_config() -> Dict[str, Any]:
    """获取默认配置

    Returns:
        Dict[str, Any]: 默认配置字典
    """
    return {
        "output": {
            "path": "./output",
            "data": "./output",
            "videos": "./output"
        },
        "recording": {
            "enabled": True,
            "event_queue_size": 10000
        },
        "video": {
            "enabled": True,
            "framerate": 30,
            "output_quality": 85
        },
        "ui_detection": {
            "enabled": True,
            "confidence_threshold": 0.7,
            "element_detection_frequency": 0.1
        }
    }
