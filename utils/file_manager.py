"""文件管理器

提供通用的文件操作工具。
"""
from pathlib import Path
from typing import Optional, List
from datetime import datetime
import os
import shutil


class FileManager:
    """文件管理器

    提供文件创建、清理、目录管理等基本操作。
    """

    def __init__(self, base_dir: str = "."):
        """初始化文件管理器

        Args:
            base_dir: 基础目录
        """
        self.base_dir = Path(base_dir)

    def ensure_directory(self, *path_parts: str) -> Path:
        """确保目录存在

        Args:
            *path_parts: 目录路径部分

        Returns:
            Path: 完整目录路径
        """
        directory = self.base_dir.joinpath(*path_parts)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    def create_temp_file(self, prefix: str = "", suffix: str = ".tmp") -> Path:
        """创建临时文件

        Args:
            prefix: 文件前缀
            suffix: 文件后缀

        Returns:
            Path: 临时文件路径
        """
        return self.ensure_directory("temp") / f"{prefix}{datetime.now().timestamp()}{suffix}"

    def cleanup_directory(self, directory: str, max_age_hours: int = 24) -> int:
        """清理目录中超过指定时间的文件

        Args:
            directory: 目录路径
            max_age_hours: 最大保留时间（小时）

        Returns:
            int: 清理的文件数量
        """
        dir_path = self.base_dir.joinpath(directory)
        if not dir_path.exists():
            return 0

        count = 0
        now = datetime.now()

        for file_path in dir_path.iterdir():
            if file_path.is_file():
                age = now - datetime.fromtimestamp(file_path.stat().st_mtime)
                if age.total_seconds() > max_age_hours * 3600:
                    file_path.unlink()
                    count += 1

        return count

    def find_files_by_pattern(self, pattern: str, directory: str = "data") -> List[Path]:
        """按模式查找文件

        Args:
            pattern: 文件名模式（如 "*.csv"）
            directory: 目录名

        Returns:
            List[Path]: 匹配的文件列表
        """
        dir_path = self.base_dir.joinpath(directory)
        if not dir_path.exists():
            return []

        return list(dir_path.glob(pattern))
