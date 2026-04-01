"""窗口信息监控器

基于pywin32获取鼠标操作时的窗口信息，包括窗口句柄、标题、类名、控件信息等。
"""
import pywintypes
import win32gui
import win32con
import win32api
import win32process
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


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
    relative_coordinates: dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0})  # 相对于屏幕坐标的窗口坐标{x: left, y: top, width: width, height: height}
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
            "extended_style": self.extended_style,
            "relative_coordinates": self.relative_coordinates
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
        relative_coordinates: 相对于窗口的控件坐标{x: left, y: top, width: width, height: height}
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
    relative_coordinates: dict[str, int] = field(default_factory=lambda: {"x": 0, "y": 0, "width": 0, "height": 0})  # 相对于屏幕坐标的窗口坐标(left, top, width, height)

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
            "rect": self.rect,
            "relative_coordinates": self.relative_coordinates
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
        
    def get_control_relative_info(self, ctrHandle: int, ctrRect: tuple[int, int, int, int]) -> dict:
        """
        根据控件 rect 获取：
        1. 相对于父窗体客户区的 x, y 坐标
        2. 控件自身的宽度、高度
        
        返回格式：
        {
            "x": 相对窗体X,
            "y": 相对窗体Y,
            "width": 宽度,
            "height": 高度
        }
        """
        if not ctrRect :
            return {"x": 0, "y": 0, "width": 0, "height": 0}

        # 控件屏幕绝对坐标
        left, top, right, bottom = ctrRect

        # 获取控件所在的根窗口（窗体）
        try:
            root_hwnd = win32gui.GetAncestor(ctrHandle, 2)  # GA_ROOT
            # 获取窗口客户区左上角的屏幕坐标
            client_x_screen, client_y_screen = win32gui.ClientToScreen(root_hwnd, (0, 0))
        except:
            client_x_screen = 0
            client_y_screen = 0

        # 计算相对坐标
        rel_x = left - client_x_screen
        rel_y = top - client_y_screen

        # 计算控件宽高
        width = right - left
        height = bottom - top

        return {
            "x": rel_x,
            "y": rel_y,
            "width": width,
            "height": height
        }

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

            # 计算窗口相对于屏幕的坐标
            window_rect = {
                "x": rect[0],
                "y": rect[1],
                "width": rect[2] - rect[0],
                "height": rect[3] - rect[1]
            }

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
                relative_coordinates=window_rect,
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

    # 定义读取控件文本的函数（兼容 GetWindowText 和 BM_GETTEXT）
    def get_control_text(self, hwnd):
         # 方法1：普通获取
        text = win32gui.GetWindowText(hwnd)
        if text:
            return text.strip()

        # 方法2：发送 WM_GETTEXT 消息（兼容所有按钮）
        try:
            buffer = bytes(256)
            length = win32api.SendMessage(
                hwnd, 
                win32con.WM_GETTEXT,  # ✅ 正确常量
                255, 
                buffer
            )
            text = buffer.decode('utf-8').strip('\x00').strip()
        except:
            text = ""
        return text

    def get_window_controls(self, window_handle: int) -> List[ControlInfo]:
        """获取窗口中的控件信息

        Args:
            window_handle: 窗口句柄

        Returns:
            List[ControlInfo]: 控件信息列表
        """
        controls = []

        root_handle = win32gui.GetAncestor(window_handle, 2)
        # 验证：获取根窗口标题
        root_title = win32gui.GetWindowText(root_handle)

        try:
            # 枚举窗口控件
            def enum_child_proc(hwnd, param):
                # 获取控件样式
                style = win32gui.GetWindowLong(hwnd, win32con.GWL_STYLE)
                
                # 检查控件是否可见
                is_visible = win32gui.IsWindowVisible(hwnd)
                
                if is_visible:
                    # text = win32gui.GetWindowText(hwnd)
                    text = self.get_control_text(hwnd)
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
                        rect=rect,
                        relative_coordinates=self.get_control_relative_info(hwnd, rect)
                    )
                    
                    controls.append(control_info)
                    win32gui.EnumChildWindows(hwnd, enum_child_proc, 0)
                
                return True  # 继续枚举

            win32gui.EnumChildWindows(root_handle, enum_child_proc, 0)

        except Exception as e:
            print(f"获取窗口控件信息失败: {e}")
        # if root_title=="模拟用户行为自动化工具 v1.0.0":
        #     print(f"[Monitor] 共{len(controls)}个控件, 详情如下：{controls}")


        return controls

    def get_hovered_control_info(self, require_text: bool = False) -> Optional[ControlInfo]:
        """获取鼠标悬停位置的最匹配控件信息（优先最内层/最小范围控件）

        Args:
            require_text: 是否要求控件必须有文本内容（默认False）

        Returns:
            Optional[ControlInfo]: 最匹配的控件信息，无匹配则返回None
        """
        try:
            # 获取鼠标当前位置
            x, y = win32api.GetCursorPos()

            # 获取鼠标位置对应的顶层窗口
            window_handle = win32gui.WindowFromPoint((x, y))
            if not window_handle:
                return None

            # 获取窗口的所有子控件（包含嵌套控件）
            all_controls = self.get_window_controls(window_handle)
            if not all_controls:
                # 无控件时返回窗口本身（保留原有逻辑，但优先子控件）
                window_info = self._get_window_info(window_handle)
                window_rect = win32gui.GetWindowRect(window_handle)
                window_as_control = ControlInfo(
                    handle=window_info.handle,
                    class_name=window_info.class_name,
                    text=window_info.title,
                    caption=window_info.title,
                    is_enabled=window_info.enabled,
                    is_visible=window_info.visible,
                    rect=window_rect,
                    relative_coordinates=self.get_control_relative_info(window_handle, window_rect)
                )
                if require_text and not window_info.title.strip():
                    return None
                return window_as_control

            # 筛选：只保留包含鼠标坐标的有效控件
            matched_controls = []
            for control in all_controls:
                left, top, right, bottom = control.rect
                
                # 验证控件矩形有效性 + 鼠标是否在控件范围内
                if (right > left and bottom > top and 
                    left <= x <= right and top <= y <= bottom):
                    
                    # 如果要求文本，过滤无有效文本的控件
                    if require_text and not (control.text and control.text.strip()):
                        continue
                    
                    matched_controls.append(control)

            if not matched_controls:
                # 无匹配子控件时返回窗口本身
                window_info = self._get_window_info(window_handle)
                window_rect = win32gui.GetWindowRect(window_handle)
                window_as_control = ControlInfo(
                    handle=window_info.handle,
                    class_name=window_info.class_name,
                    text=window_info.title,
                    caption=window_info.title,
                    is_enabled=window_info.enabled,
                    is_visible=window_info.visible,
                    rect=window_rect,
                    relative_coordinates=self.get_control_relative_info(window_handle, window_rect)
                )
                if require_text and not window_info.title.strip():
                    return None
                return window_as_control

            # 排序：优先选择最小范围的控件（面积越小优先级越高）
            # 替代GetAncestry的层级判断：通过父控件递归计数判断嵌套深度
            def get_control_depth(hwnd: int) -> int:
                """计算控件嵌套深度（替代GetAncestry）"""
                depth = 0
                current = hwnd
                while True:
                    parent = win32gui.GetParent(current)
                    if parent and parent != window_handle:  # 直到窗口根句柄为止
                        depth += 1
                        current = parent
                    else:
                        break
                return depth

            def calculate_control_area(control: ControlInfo) -> int:
                """计算控件矩形面积"""
                left, top, right, bottom = control.rect
                return (right - left) * (bottom - top)

            # 排序规则：1. 面积升序（越小越精准） 2. 嵌套深度降序（越深越内层）
            matched_controls.sort(key=lambda c: (
                calculate_control_area(c),
                -get_control_depth(c.handle)
            ))

            # 返回最匹配的第一个控件
            return matched_controls[0]

        except pywintypes.error as e:
            print(f"Windows API调用错误（获取悬停控件）: {e}")
            return None
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
                        rect=window_info.rect,
                        relative_coordinates=self.get_control_relative_info(window_handle, window_info.rect)    
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
                    rect=(0, 0, 0, 0),
                    relative_coordinates={"x": 0, "y": 0, "width": 0, "height": 0}
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
                rect=(0, 0, 0, 0),
                relative_coordinates={"x": 0, "y": 0, "width": 0, "height": 0}
            )


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