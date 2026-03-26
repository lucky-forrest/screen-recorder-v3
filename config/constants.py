"""项目常量定义

集中管理所有硬编码的魔法数字和配置值。
"""
from typing import Final


# GUI窗口配置
class GUIConfig:
    """GUI窗口配置常量"""

    WINDOW_WIDTH: Final[int] = 1000
    WINDOW_HEIGHT: Final[int] = 700
    PANEL_PADDING: Final[str] = "10"
    CONTROL_BUTTON_WIDTH: Final[str] = "15"
    STATUS_TEXT_UPDATE_INTERVAL: Final[int] = 10  # 10ms


# UI分析器配置
class UIAnalysisConfig:
    """UI分析器配置常量"""

    ANALYSIS_INTERVAL: Final[float] = 0.1  # 秒
    DEFAULT_CONFIDENCE_THRESHOLD: Final[float] = 0.7


# 视频生成器配置
class VideoConfig:
    """视频生成器配置常量"""

    VIDEO_CODEC: Final[str] = "mp4v"
    FRAME_DELAY_SECONDS: Final[float] = 0.05
    MINIMUM_FILE_SIZE: Final[int] = 10240  # 10KB


# 元素检测器配置
class ElementDetectorConfig:
    """元素检测器配置常量"""

    # 文本框检测阈值
    CONTRAST_THRESHOLD: Final[float] = 0.1
    EDGE_DENSITY_THRESHOLD: Final[float] = 0.05

    # 按钮检测阈值
    COMPACTNESS_THRESHOLD: Final[float] = 0.1

    # 下拉框检测阈值
    ARROW_REGION_RATIO: Final[float] = 0.7
    ARROW_REGION_WIDTH: Final[int] = 10


# 系统配置
class SystemConfig:
    """系统配置常量"""

    SESSION_ID_FORMAT: Final[str] = "%Y%m%d_%H%M%S"
    MAX_EVENT_QUEUE_SIZE: Final[int] = 10000
