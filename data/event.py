
# -*- coding: utf-8 -*-
"""操作事件数据类

定义键盘、鼠标、UI等操作事件的数据结构。
"""
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional


class EventType(Enum):
    """事件类型枚举"""
    KEY_PRESS = "key_press"
    KEY_RELEASE = "key_release"
    MOUSE_MOVE = "mouse_move"
    MOUSE_CLICK = "mouse_click"
    MOUSE_SCROLL = "mouse_scroll"
    WINDOW_CHANGE = "window_change"
    UI_ELEMENT_INTERACTION = "ui_element_interaction"


class MouseButton(Enum):
    """鼠标按钮枚举"""
    LEFT = "left"
    RIGHT = "right"
    MIDDLE = "middle"


class UIElementType(Enum):
    """UI元素类型枚举"""
    TEXTBOX = "textbox"
    BUTTON = "button"
    DROPDOWN = "dropdown"
    COMBOBOX = "combobox"
    CHECKBOX = "checkbox"
    RADIO_BUTTON = "radio_button"
    MENU_ITEM = "menu_item"
    TEXT_LABEL = "text_label"
    OTHER = "other"


@dataclass
class EventGroup:
    """事件分组类（用于测试用例）"""
    key_events: list = field(default_factory=list)
    mouse_events: list = field(default_factory=list)
    window_events: list = field(default_factory=list)


@dataclass
class KeyboardEvent:
    """键盘事件类

    Attributes:
        key: 按下的键字符
        modifier: 按下的修饰键（Ctrl, Alt, Shift）
        event_type: 事件类型（按下/释放）
        timestamp: 时间戳
    """
    key: str
    modifier: tuple[str, ...]
    event_type: str  # "press" or "release"
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后验证数据"""
        if self.event_type not in ("press", "release"):
            raise ValueError(f"Invalid event_type: {self.event_type}")


@dataclass
class MouseEvent:
    """鼠标事件类

    Attributes:
        event_type: 事件类型
        x: X坐标
        y: Y坐标
        button: 鼠标按钮
        scroll_delta: 滚轮滚动距离（滚动事件时有效）
        timestamp: 时间戳
    """
    event_type: EventType
    x: int
    y: int
    button: Optional[MouseButton] = None
    scroll_delta: int = 0
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        """初始化后验证数据"""
        if self.event_type == EventType.MOUSE_CLICK and self.button is None:
            raise ValueError("Button is required for MOUSE_CLICK events")


@dataclass
class WindowEvent:
    """窗口事件类

    Attributes:
        window_title: 窗口标题
        process_name: 进程名
        timestamp: 时间戳
    """
    window_title: str
    process_name: str
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UIElementInfo:
    """UI元素信息类

    Attributes:
        element_type: 元素类型
        element_content: 元素文本内容
        bounding_box: 元素边界框 (left, top, right, bottom)
        confidence: 识别置信度 (0-1)
        state: 元素状态
        timestamp: 时间戳
    """
    element_type: UIElementType
    element_content: Optional[str] = None
    bounding_box: Optional[tuple[int, int, int, int]] = None
    confidence: float = 0.0
    state: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    def is_confident(self, threshold: float = 0.7) -> bool:
        """判断识别是否达到置信度"""
        return self.confidence >= threshold


@dataclass
class WindowSpecificInfo:
    """窗口特定信息类

    包含鼠标操作时的窗口和控件信息。

    Attributes:
        window_handle: 窗口句柄
        window_title: 窗口标题
        window_class_name: 窗口类名
        window_process_id: 进程ID
        window_process_name: 进程名称
        window_visible: 窗口是否可见
        window_enabled: 窗口是否启用
        window_active: 窗口是否是活动窗口
        control_handle: 控件句柄
        control_class_name: 控件类名
        control_text: 控件文本
    """
    window_handle: int = 0
    window_title: str = ""
    window_class_name: str = ""
    window_process_id: int = 0
    window_process_name: str = ""
    window_visible: bool = False
    window_enabled: bool = False
    window_active: bool = False
    control_handle: int = 0
    control_class_name: str = ""
    control_text: str = ""
    rect: tuple[int, int, int, int] = (0, 0, 0, 0)  # (left, top, right, bottom)，可用于检测是否为有效值

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "window_handle": self.window_handle,
            "window_title": self.window_title,
            "window_class_name": self.window_class_name,
            "window_process_id": self.window_process_id,
            "window_process_name": self.window_process_name,
            "window_visible": self.window_visible,
            "window_enabled": self.window_enabled,
            "window_active": self.window_active,
            "control_handle": self.control_handle,
            "control_class_name": self.control_class_name,
            "control_text": self.control_text,
            "rect": self.rect if self.rect and all(v > 0 for v in self.rect) else (0, 0, 0, 0)
        }


@dataclass
class OperationEvent:
    """综合操作事件类

    包含键盘、鼠标和UI元素的完整信息。

    Attributes:
        event_type: 核心事件类型
        detail: 详细信息
        coordinates: (x, y) 坐标
        window_title: 当前活动窗口标题
        element_info: UI元素信息
        window_info: 窗口特定信息（句柄、类名、控件信息等）
        application_name: 应用程序名称（录制时指定）
        context: 上下文信息
        timestamp: 时间戳
        operation_category: 操作分类
        show_behavior_marker: 是否显示行为标记
    """
    event_type: EventType
    detail: str
    coordinates: tuple[int, int]
    window_title: Optional[str] = None
    element_info: Optional[UIElementInfo] = None
    window_info: Optional[WindowSpecificInfo] = None
    application_name: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    operation_category: Optional[str] = None
    show_behavior_marker: bool = True

    def get_export_dict(self) -> Dict[str, Any]:
        """获取导出字典，包含所有窗口信息（17个字段与CSV头一致）"""
        result = {
            "time": self.timestamp.isoformat(),
            "type": self.event_type.value,
            "detail": self.detail,
            "x": self.coordinates[0],
            "y": self.coordinates[1],
            "window_title": self.window_title or "",
            "element_type": self.element_info.element_type.value if self.element_info else "",
            "element_content": self.element_info.element_content if self.element_info else "",
            "window_handle": 0,
            "window_class_name": "",
            "window_process_id": 0,
            "window_process_name": "",
            "window_visible": False,
            "window_enabled": False,
            "window_active": False,
            "control_handle": 0,
            "control_class_name": "",
            "control_text": "",
            "rect": self.element_info.bounding_box if self.element_info and self.element_info.bounding_box else None,
        }

        # 添加窗口信息
        if self.window_info:
            window_info = self.window_info.to_dict()
            result.update(window_info)

        return result

    def get_full_json(self) -> Dict[str, Any]:
        """获取完整的JSON格式（包含所有上下文和数据）
        注意：返回的字典键顺序必须与JSON导出的字段顺序一致！
        """
        event_data = {
            "time": self.timestamp.isoformat(),
            "type": self.event_type.value,
            "x": self.coordinates[0],
            "y": self.coordinates[1],
            "window_title": self.window_title or "",
            "element_type": self.element_info.element_type.value if self.element_info else "",
            "element_content": self.element_info.element_content if self.element_info else "",
            "detail": self.detail,
            "operation_category": self.operation_category or "",
            "show_behavior_marker": self.show_behavior_marker,
            "window_handle": 0,
            "window_class_name": "",
            "window_process_id": 0,
            "window_process_name": "",
            "window_visible": False,
            "window_enabled": False,
            "window_active": False,
            "control_handle": 0,
            "control_class_name": "",
            "control_text": "",
            "application_name": self.application_name or "",
            "rect": self.element_info.bounding_box if self.element_info and self.element_info.bounding_box else None,

        }

        if self.element_info:
            event_data["element_confidence"] = self.element_info.confidence
            event_data["element_state"] = self.element_info.state
            event_data["rect"] = self.element_info.bounding_box

        if self.window_info:
            event_data.update(self.window_info.to_dict())

        return event_data


class SessionStartEvent:
    """录制会话开始事件"""

    def __init__(self, session_id: str):
        """初始化会话开始事件

        Args:
            session_id: 会话ID（格式：YYYYMMDD_HHMMSS）
        """
        self.session_id = session_id
        self.start_time = datetime.now()


class SessionEndEvent:
    """录制会话结束事件"""

    def __init__(self, session_id: str, total_events: int):
        """初始化会话结束事件

        Args:
            session_id: 会话ID
            total_events: 录制的事件总数
        """
        self.session_id = session_id
        self.end_time = datetime.now()
        self.total_events = total_events
