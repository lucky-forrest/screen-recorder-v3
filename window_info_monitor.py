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

            # 如果窗口标题为空，尝试获取父窗口或Owner窗口
            if not window_info.title:
                window_info = self._get_owner_window_info(handle)

            # 如果仍然没有标题，尝试使用窗口类名作为标识
            if not window_info.title:
                window_info.title = f"[{window_info.class_name}]"

            return window_info

        except Exception as e:
            print(f"获取窗口信息失败: {e}")
            import traceback
            traceback.print_exc()
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
            # 获取窗口类名（先获取）
            class_name = win32gui.GetClassName(handle)

            # 获取窗口标题
            title = win32gui.GetWindowText(handle)

            # 如果标题为空，尝试获取父窗口信息来获取标题
            if not title:
                try:
                    parent_handle = win32gui.GetParent(handle)
                    if parent_handle:
                        parent_info = self._get_window_info(parent_handle)
                        title = parent_info.title
                except Exception as e:
                    print(f"获取父窗口标题失败: {e}")

            # 如果仍然没有标题，使用窗口类名作为标识
            if not title:
                title = f"[{class_name}]"

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
            import traceback
            traceback.print_exc()
            # 尝试使用缓存
            window_info = self._window_cache.get(handle, None)
            if window_info:
                return window_info
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
        except Exception as e:
            print(f"获取窗口信息时发生意外错误: {e}")
            import traceback
            traceback.print_exc()
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
            def enum_child_proc(hwnd, param):
                # 获取控件样式
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                
                # 检查控件是否可见
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                if is_visible:
                    text = win32gui.GetWindowText(hwnd)
                    class_name = win32gui.GetClassName(hwnd)
                    rect = win32gui.GetWindowRect(hwnd)
                    
                    control_info = ControlInfo(
                        handle=hwnd,
                        class_name=class_name,
                        style=style,
                        text=text,
                        caption=text if text else class_name,
                        is_enabled=win32gui.IsWindowEnabled(hwnd),
                        is_visible=is_visible,
                        rect=rect
                    )
                    
                    controls.append(control_info)
                
                return True  # 继续枚举

            win32gui.EnumChildWindows(window_handle, enum_child_proc, 0)

        except Exception as e:
            print(f"获取窗口控件信息失败: {e}")

        return controls

    def get_hovered_control_info(self, require_text: bool = False) -> Optional[ControlInfo]:
        """获取鼠标悬停位置的控件信息

        Args:
            require_text: 是否要求控件必须有文本内容（默认False）

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

            # 获取窗口的所有子控件
            all_controls = self.get_window_controls(window_handle)
            
            # 查找包含鼠标位置的控件
            for control in all_controls:
                left, top, right, bottom = control.rect
                if left <= x <= right and top <= y <= bottom:
                    # 如果要求文本内容，检查控件是否有文本
                    if require_text and not control.text:
                        continue
                    return control
            
            # 如果没有找到子控件，返回窗口本身作为控件
            # 获取窗口本身的详细信息
            window_info = self._get_window_info(window_handle)
            window_rect = win32gui.GetWindowRect(window_handle)
            
            window_as_control = ControlInfo(
                handle=window_info.handle,
                class_name=window_info.class_name,
                text=window_info.title,
                caption=window_info.title,
                is_enabled=window_info.enabled,
                is_visible=window_info.visible,
                rect=window_rect
            )
            
            # 如果要求文本内容，检查窗口标题
            if require_text and not window_info.title:
                return None
                
            return window_as_control

        except Exception as e:
            print(f"获取悬停控件信息失败: {e}")
            import traceback
            traceback.print_exc()
            return None

    def get_window_info_at_position(self, x: int, y: int) -> dict:
        """获取指定位置的窗口信息和控件信息

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            dict: 包含窗口信息和控件信息的字典
        """
        result = {"window_info": None, "control_info": None}

        try:
            # 获取鼠标位置对应的窗口
            window_handle = win32gui.WindowFromPoint((x, y))

            if window_handle:
                # 获取窗口信息
                window_info = self._get_window_info(window_handle)
                result["window_info"] = window_info

                # 获取鼠标位置的控件信息
                control_info = self.get_hovered_control_info(require_text=False)
                if control_info and control_info.handle != window_info.handle:
                    # 如果控件不是窗口本身，使用控件信息
                    result["control_info"] = control_info
                else:
                    # 否则使用窗口信息作为控件信息
                    control_info = ControlInfo(
                        handle=window_info.handle,
                        class_name=window_info.class_name,
                        text=window_info.title,
                        caption=window_info.title,
                        is_enabled=window_info.enabled,
                        is_visible=window_info.visible,
                        rect=window_info.rect
                    )
                    result["control_info"] = control_info

        except Exception as e:
            print(f"获取位置({x}, {y})的窗口信息失败: {e}")
            import traceback
            traceback.print_exc()

        return result

    def get_active_window_info(self) -> WindowInfo:
        """获取当前活动窗口的信息（用于键盘事件等没有坐标的事件）

        Returns:
            WindowInfo: 当前活动窗口信息
        """
        try:
            handle = win32gui.GetForegroundWindow()
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
            return self._get_window_info(handle)
        except Exception as e:
            print(f"获取活动窗口信息失败: {e}")
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


# 全局单例
_window_monitor: Optional[WindowInfoMonitor] = None


def get_active_window_info(self) -> WindowInfo:
    """获取当前活动窗口的信息（用于键盘事件等没有坐标的事件）

    Returns:
        WindowInfo: 当前活动窗口信息
    """
    try:
        handle = win32gui.GetForegroundWindow()
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
        return self._get_window_info(handle)
    except Exception as e:
        print(f"获取活动窗口信息失败: {e}")
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


def get_monitor() -> WindowInfoMonitor:
    """获取窗口监控器单例

    Returns:
        WindowInfoMonitor: 窗口监控器实例
    """
    global _window_monitor
    if _window_monitor is None:
        _window_monitor = WindowInfoMonitor()
    return _window_monitor


# 测试代码
if __name__ == "__main__":
    monitor = get_monitor()
    
    print("=== 测试获取当前鼠标位置的窗口信息 ===")
    current_window = monitor.get_current_window_info()
    print(f"窗口标题: {current_window.title}")
    print(f"窗口类名: {current_window.class_name}")
    print(f"进程名称: {current_window.process_name}")
    print(f"窗口句柄: {current_window.handle}")
    
    print("\n=== 测试获取当前鼠标位置的控件信息 ===")
    current_control = monitor.get_hovered_control_info()
    if current_control:
        print(f"控件类名: {current_control.class_name}")
        print(f"控件文本: {current_control.text}")
        print(f"控件句柄: {current_control.handle}")
    else:
        print("未找到控件")
    
    print("\n=== 测试获取鼠标位置的窗口和控件信息 ===")
    x, y = win32api.GetCursorPos()
    pos_result = monitor.get_window_info_at_position(x, y)
    if pos_result["window_info"]:
        print(f"窗口标题: {pos_result['window_info'].title}")
    if pos_result["control_info"]:
        print(f"控件文本: {pos_result['control_info'].text}")
        print(f"控件类名: {pos_result['control_info'].class_name}")
    
    print("\n=== 测试获取窗口的所有控件 ===")
    if current_window.handle:
        controls = monitor.get_window_controls(current_window.handle)
        print(f"找到 {len(controls)} 个控件:")
        for i, control in enumerate(controls[:5]):  # 只显示前5个
            print(f"  {i+1}. 类名: {control.class_name}, 文本: '{control.text}'")