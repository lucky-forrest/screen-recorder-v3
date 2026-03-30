"""窗口信息监控器

基于pywin32获取鼠标操作时的窗口信息，包括窗口句柄、标题、类名、控件信息等。
"""
import pywintypes
import win32gui
import win32con
import win32api
import win32process
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class WindowInfo:
    """窗口信息类

    Attributes:
        handle: 窗口句柄
        title: 窗口标题
        class_name: 窗口类名
        process_id: 进程ID
        pid: 进程名称
        visible: 窗口是否可见
        enabled: 窗口是否启用
        active: 窗口是否是活动窗口
        rect: 窗口位置和尺寸 (left, top, right, bottom)
        style: 窗口样式
        extended_style: 扩展窗口样式
    """
    handle: int
    title: str
    class_name: str
    process_id: int
    process_name: str = ""
    visible: bool = False
    enabled: bool = False
    active: bool = False
    rect: tuple[int, int, int, int] = (0, 0, 0, 0)
    style: int = 0
    extended_style: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "handle": self.handle,
            "title": self.title,
            "class_name": self.class_name,
            "process_id": self.process_id,
            "process_name": self.process_name,
            "visible": self.visible,
            "enabled": self.enabled,
            "active": self.active,
            "rect": self.rect,
            "style": self.style,
            "extended_style": self.extended_style
        }


@dataclass
class ControlInfo:
    """控件信息类

    Attributes:
        handle: 控件句柄
        class_name: 控件类名
        style: 控件样式
        text: 控件文本
        caption: 控件标题
        is_enabled: 是否启用
        is_visible: 是否可见
        is_focused: 是否处于焦点
        rect: 控件位置和尺寸
    """
    handle: int
    class_name: str
    style: int = 0
    text: str = ""
    caption: str = ""
    is_enabled: bool = False
    is_visible: bool = False
    is_focused: bool = False
    rect: tuple[int, int, int, int] = (0, 0, 0, 0)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "handle": self.handle,
            "class_name": self.class_name,
            "style": self.style,
            "text": self.text,
            "caption": self.caption,
            "is_enabled": self.is_enabled,
            "is_visible": self.is_visible,
            "is_focused": self.is_focused,
            "rect": self.rect
        }


class WindowInfoMonitor:
    """窗口信息监控器

    提供获取当前鼠标所在窗口的信息以及窗口中控件的信息。
    """

    def __init__(self):
        """初始化窗口信息监控器"""
        self._last_window_info: Optional[WindowInfo] = None
        self._window_cache: Dict[int, WindowInfo] = {}

    def get_current_window_info(self) -> WindowInfo:
        """获取当前鼠标所在窗口的信息

        Returns:
            WindowInfo: 窗口信息
        """
        try:
            # 获取鼠标当前位置
            x, y = win32api.GetCursorPos()

            # 获取鼠标位置对应的窗口
            handle = win32gui.WindowFromPoint((x, y))

            # 如果没有找到窗口，返回空的窗口信息
            if not handle:
                return WindowInfo(
                    handle=0,
                    title="",
                    class_name="",
                    process_id=0,
                    process_name="",
                    visible=False,
                    enabled=False,
                    active=False,
                    rect=(0, 0, 0, 0)
                )

            # 获取窗口信息
            window_info = self._get_window_info(handle)

            # 如果窗口信息为空，获取父窗口或Owner窗口
            if not window_info.title:
                window_info = self._get_owner_window_info(handle)

            return window_info

        except Exception as e:
            print(f"获取窗口信息失败: {e}")
            return WindowInfo(
                handle=0,
                title="",
                class_name="",
                process_id=0,
                process_name="",
                visible=False,
                enabled=False,
                active=False,
                rect=(0, 0, 0, 0)
            )

    def _get_window_info(self, handle: int) -> WindowInfo:
        """获取窗口信息

        Args:
            handle: 窗口句柄

        Returns:
            WindowInfo: 窗口信息
        """
        try:
            # 获取窗口标题
            title = win32gui.GetWindowText(handle)
            if not title:
                title = "(无标题)"

            # 获取窗口类名
            class_name = win32gui.GetClassName(handle)

            # 获取窗口进程ID
            process_id = win32process.GetWindowThreadProcessId(handle)[1]

            # 获取窗口位置和尺寸
            rect = win32gui.GetWindowRect(handle)

            # 获取窗口样式
            style = win32gui.GetWindowLong(handle, win32con.GWL_STYLE)
            extended_style = win32gui.GetWindowLong(handle, win32con.GWL_EXSTYLE)

            # 检查窗口状态
            visible = win32gui.IsWindowVisible(handle)
            enabled = win32gui.IsWindowEnabled(handle)
            active = (handle == win32gui.GetForegroundWindow())

            # 获取进程名称
            process_name = self._get_process_name(process_id)

            window_info = WindowInfo(
                handle=handle,
                title=title,
                class_name=class_name,
                process_id=process_id,
                process_name=process_name,
                visible=visible,
                enabled=enabled,
                active=active,
                rect=rect,
                style=style,
                extended_style=extended_style
            )

            # 缓存窗口信息
            self._window_cache[handle] = window_info
            return window_info

        except pywintypes.error as e:
            print(f"获取窗口信息失败 (handle={handle}): {e}")
            # 尝试使用缓存
            return self._window_cache.get(handle, WindowInfo(0, "", "", 0, ""))
        except Exception as e:
            print(f"获取窗口信息时发生意外错误: {e}")
            return WindowInfo(0, "", "", 0, "")

    def _get_owner_window_info(self, handle: int) -> WindowInfo:
        """获取拥有者窗口信息

        Args:
            handle: 窗口句柄

        Returns:
            WindowInfo: 窗口信息
        """
        try:
            # 获取父窗口
            parent = win32gui.GetParent(handle)
            if parent:
                return self._get_window_info(parent)

            # 获取Owner窗口
            owner = win32gui.GetWindow(handle, win32con.GW_OWNER)
            if owner:
                return self._get_window_info(owner)

            return WindowInfo(0, "", "", 0, "")

        except Exception as e:
            print(f"获取拥有者窗口信息失败: {e}")
            return WindowInfo(0, "", "", 0, "")

    def _get_process_name(self, process_id: int) -> str:
        """获取进程名称

        Args:
            process_id: 进程ID

        Returns:
            str: 进程名称
        """
        try:
            import psutil
            process = psutil.Process(process_id)
            return process.name()
        except ImportError:
            # 如果没有psutil，返回进程ID作为进程名
            return str(process_id)
        except Exception as e:
            print(f"获取进程名称失败 (pid={process_id}): {e}")
            return str(process_id)

    def get_window_controls(self, window_handle: int) -> List[ControlInfo]:
        """获取窗口中的控件信息

        Args:
            window_handle: 窗口句柄

        Returns:
            List[ControlInfo]: 控件信息列表
        """
        controls = []

        try:
            # 枚举窗口控件
            def callback(hwnd, extra_data):
                # 获取控件样式
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)

                # 检查是否是可交互控件（忽略系统按钮等）
                # 可交互的控件通常有BS_*样式
                is_container = bool(style & 0x40000000)  # BS_GROUPBOX
                is_button = bool(style & 0x80000000)     # BS_DEFPUSHBUTTON

                # 只获取可见且启用的控件或重要容器
                if win32gui.IsWindowVisible(hwnd):
                    if is_container or is_button:
                        text = win32gui.GetWindowText(hwnd)
                        caption = text if text else win32gui.GetClassName(hwnd)

                        rect = win32gui.GetWindowRect(hwnd)

                        control_info = ControlInfo(
                            handle=hwnd,
                            class_name=win32gui.GetClassName(hwnd),
                            style=style,
                            text=text,
                            caption=caption,
                            is_enabled=win32gui.IsWindowEnabled(hwnd),
                            is_visible=True,
                            rect=rect
                        )

                        controls.append(control_info)

                return True

            win32gui.EnumChildWindows(window_handle, callback, None)

        except Exception as e:
            print(f"获取窗口控件信息失败: {e}")

        return controls

    def get_hovered_control_info(self) -> Optional[ControlInfo]:
        """获取鼠标悬停位置的控件信息

        Returns:
            Optional[ControlInfo]: 控件信息，如果没有找到则返回None
        """
        try:
            # 获取鼠标当前位置
            x, y = win32api.GetCursorPos()

            # 获取鼠标位置对应的窗口
            window_handle = win32gui.WindowFromPoint((x, y))

            if not window_handle:
                return None

            # 直接检索鼠标位置对应的控件
            control_handle = win32gui.WindowFromPoint((x, y))

            if not control_handle:
                return None

            # 检查该控件是否是窗口的子控件
            parent = win32gui.GetParent(control_handle)

            # 如果是直接在窗口上点击的控件，或者该控件的父窗口是我们感兴趣的窗口
            if parent == window_handle or win32gui.GetParent(window_handle) == control_handle:
                # 使用WindowFromPoint获取到的通常是更精细的控件
                control_handle = window_handle

            style = win32gui.GetWindowLong(control_handle, win32con.GWL_STYLE)

            # 检查是否是有效的交互控件
            is_valid_control = (
                win32gui.IsWindowVisible(control_handle) and
                win32gui.IsWindowEnabled(control_handle) and
                win32gui.GetWindowText(control_handle)
            )

            if not is_valid_control:
                return None

            rect = win32gui.GetWindowRect(control_handle)
            text = win32gui.GetWindowText(control_handle)
            caption = text if text else win32gui.GetClassName(control_handle)

            control_info = ControlInfo(
                handle=control_handle,
                class_name=win32gui.GetClassName(control_handle),
                style=style,
                text=text,
                caption=caption,
                is_enabled=True,
                is_visible=True,
                rect=rect
            )

            return control_info

        except Exception as e:
            print(f"获取悬停控件信息失败: {e}")
            return None


# 全局单例
_window_monitor: Optional[WindowInfoMonitor] = None


def get_monitor() -> WindowInfoMonitor:
    """获取窗口监控器单例

    Returns:
        WindowInfoMonitor: 窗口监控器实例
    """
    global _window_monitor
    if _window_monitor is None:
        _window_monitor = WindowInfoMonitor()
    return _window_monitor
