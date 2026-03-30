"""路径管理工具

统一管理配置文件路径，确保所有输出文件按照config.json的配置存放。
"""
from pathlib import Path
from typing import Optional
from utils.file_manager import FileManager


class PathManager:
    """路径管理器

    根据config.json中output配置统一管理所有输出文件路径。
    """

    def __init__(self, config_path: str = "config.json"):
        """初始化路径管理器

        Args:
            config_path: 配置文件路径
        """
        import utils.config_loader as config_loader
        self.config = config_loader.load_config(config_path)
        self._output_dir: Optional[Path] = None

    def get_output_directory(self) -> Path:
        """获取输出目录base path

        Returns:
            Path: 输出目录的基础路径
        """
        if self._output_dir is None:
            self._output_dir = self._get_output_base_dir()
        return self._output_dir

    def get_csv_directory(self) -> Path:
        """获取CSV文件目录

        Returns:
            Path: CSV输出目录
        """
        csv_path = self.config.get("output", {}).get("csv", "./output")
        return Path(csv_path)

    def get_json_directory(self) -> Path:
        """获取JSON文件目录

        Returns:
            Path: JSON输出目录
        """
        json_path = self.config.get("output", {}).get("json", "./output")
        return Path(json_path)

    def get_video_directory(self) -> Path:
        """获取视频文件目录

        Returns:
            Path: 视频输出目录
        """
        video_path = self.config.get("output", {}).get("mp4", "./output")
        return Path(video_path)

    def _get_output_base_dir(self) -> Path:
        """获取输出目录的基础路径（兼容旧配置格式）"""
        # 优先使用新的output配置
        if self.config.get("output"):
            output_config = self.config["output"]

            # 如果CSV、JSON、MP4配置指向同一目录，则使用该目录
            csv_dir = output_config.get("csv", None)
            json_dir = output_config.get("json", None)
            mp4_dir = output_config.get("mp4", None)

            if csv_dir and json_dir and mp4_dir and csv_dir == json_dir == mp4_dir:
                base_dir = Path(csv_dir)
            else:
                # 如果配置不同，使用CSV目录作为base，创建子目录
                base_dir = Path(csv_dir)
        else:
            # 兼容旧格式
            output_config = self.config.get("output", {})
            base_dir = Path(output_config.get("data", self.config.get("paths", {}).get("data", "./output")))

        base_dir.mkdir(parents=True, exist_ok=True)
        return base_dir

    def get_csv_file_path(self, session_id: str) -> Path:
        """获取CSV文件完整路径

        Args:
            session_id: 会话ID

        Returns:
            Path: CSV文件路径
        """
        csv_dir = self.get_csv_directory()
        return csv_dir / f"{session_id}_operation_log.csv"

    def get_json_file_path(self, session_id: str) -> Path:
        """获取JSON文件完整路径

        Args:
            session_id: 会话ID

        Returns:
            Path: JSON文件路径
        """
        json_dir = self.get_json_directory()
        return json_dir / f"{session_id}_operation_log.json"

    def get_video_file_path(self, session_id: str) -> Path:
        """获取视频文件完整路径

        Args:
            session_id: 会话ID

        Returns:
            Path: 视频文件路径
        """
        video_dir = self.get_video_directory()
        return video_dir / f"{session_id}_operation_video.mp4"

    def ensure_directories_exist(self) -> dict[str, Path]:
        """确保所有输出目录存在

        Returns:
            dict: 创建的目录路径字典，包含 csv, json, mp4
        """
        paths = {
            "csv": self.get_csv_directory(),
            "json": self.get_json_directory(),
            "mp4": self.get_video_directory()
        }

        for key, path in paths.items():
            path.mkdir(parents=True, exist_ok=True)

        return paths

    def get_message_directory(self, message_name: str) -> Path:
        """获取基于消息名称的输出目录

        Args:
            message_name: 录制消息名称（会过滤非法字符）

        Returns:
            Path: 消息名称对应的输出目录路径
        """
        output_base = self.get_output_directory()
        sanitized_name = FileManager.sanitize_filename(message_name)
        return output_base / sanitized_name

    def get_message_csv_file_path(self, message_name: str) -> Path:
        """获取基于消息名称的CSV文件完整路径

        Args:
            message_name: 录制消息名称

        Returns:
            Path: CSV文件路径
        """
        msg_dir = self.get_message_directory(message_name)
        return msg_dir / f"{message_name}_operation_log.csv"

    def get_message_json_file_path(self, message_name: str) -> Path:
        """获取基于消息名称的JSON文件完整路径

        Args:
            message_name: 录制消息名称

        Returns:
            Path: JSON文件路径
        """
        msg_dir = self.get_message_directory(message_name)
        return msg_dir / f"{message_name}_operation_log.json"

    def get_message_video_file_path(self, message_name: str) -> Path:
        """获取基于消息名称的视频文件完整路径

        Args:
            message_name: 录制消息名称

        Returns:
            Path: 视频文件路径
        """
        msg_dir = self.get_message_directory(message_name)
        return msg_dir / f"{message_name}_operation_video.mp4"
