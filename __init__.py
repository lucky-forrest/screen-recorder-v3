"""Advanced Computer Operation Recorder

一个强大的电脑操作记录工具，能够智能识别UI元素并详细记录用户的交互行为。
"""

__version__ = "1.0.0"
__author__ = "AI Developer"
__license__ = "MIT"

from .data.event import (
    OperationEvent,
    EventType,
    UIElementType
)
from .recorder_engine import RecorderEngine
from .video_generator import VideoGenerator
from .gui import OperationRecorderGUI

__all__ = [
    "OperationEvent",
    "EventType",
    "UIElementType",
    "RecorderEngine",
    "VideoGenerator",
    "OperationRecorderGUI"
]
