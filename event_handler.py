"""设备输入事件处理器

负责监听和捕获键盘、鼠标输入事件，提供统一的回调接口。
"""
import threading
from queue import Queue
from typing import Callable, Optional
from dataclasses import dataclass
from data.event import (
    KeyboardEvent,
    MouseEvent,
    EventType,
    MouseButton
)


@dataclass
class EventHandlerConfig:
    """事件处理器配置

    Attributes:
        keyboard_enabled: 是否启用键盘监听
        mouse_enabled: 是否启用鼠标监听
        scroll_enabled: 是否启用滚轮监听
        key_mapping: 键盘事件映射表（特殊按键）
    """
    keyboard_enabled: bool = True
    mouse_enabled: bool = True
    scroll_enabled: bool = True
    key_mapping: dict = None

    def __post_init__(self):
        """初始化默认值"""
        if self.key_mapping is None:
            self.key_mapping = {
                "space": " ",
                "enter": "\n",
                "tab": "\t",
                "escape": "\x1b",
            }


class KeyboardHandler:
    """键盘事件处理器

    使用pynput库监听键盘输入事件。
    """

    def __init__(self, config: EventHandlerConfig):
        """初始化键盘处理器

        Args:
            config: 事件处理器配置
        """
        self.config = config
        self._listener = None
        self._event_queue: Queue = Queue()
        self._callbacks: list[Callable] = []
        self._global_callbacks: list[Callable] = []
        self.is_running = False

    def register_global_callback(self, callback: Callable[[dict], None]):
        """注册全局回调函数

        Args:
            callback: 全局回调函数
        """
        self._global_callbacks.append(callback)

    def start(self):
        """启动键盘监听"""
        if self.is_running:
            print("[Keyboard Handler] Already running")
            return

        try:
            from pynput import keyboard
            print("[Keyboard Handler] Starting listener...")

            self._listener = keyboard.Listener(
                on_press=self._on_press,
                on_release=self._on_release
            )
            self._listener.start()
            self.is_running = True
            print("✓ Keyboard listener started")
        except ImportError:
            print("[ERROR] pynput library is required. Install with: pip install pynput")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to start keyboard listener: {e}")
            raise RuntimeError(f"Failed to start keyboard listener: {e}")

    def stop(self):
        """停止键盘监听"""
        if not self.is_running:
            return

        if self._listener:
            self._listener.stop()
            self._listener = None

        self.is_running = False
        print("Keyboard listener stopped")

    def on_event(self, callback: Callable[[dict], None]):
        """注册事件回调函数

        Args:
            callback: 回调函数，接收事件字典作为参数

        Example:
            def handle_key(event_dict):
                print(f"Key pressed: {event_dict}")

            handler.on_event(handle_key)
        """
        self._callbacks.append(callback)

    def _process_event(self, event: dict):
        """处理事件并触发回调"""
        # 特殊回调（专用）
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")

        # 全局回调
        for callback in self._global_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in keyboard global callback: {e}")

    def _on_press(self, key):
        """pynput键盘按下回调"""
        try:
            # 获取按键名称
            key_name = ""
            if hasattr(key, 'char'):
                key_name = key.char or ''
            else:
                char_str = str(key)
                if char_str.startswith("Key."):
                    key_name = char_str.replace("Key.", "")

            # 转换特殊按键
            key_name = self.config.key_mapping.get(key_name, key_name)

            # 构建事件字典
            event_dict = {
                'event_type': 'key_press',
                'key': key_name,
                'modifier': [],
                'press': True,
                'timestamp': datetime.now().isoformat()
            }

            # print(f"[Keyboard Handler] Event ready: {event_dict}")
            self._process_event(event_dict)

        except Exception as e:
            print(f"[ERROR] Error on key press: {e}")
            import traceback
            traceback.print_exc()

    def _on_release(self, key):
        """pynput键盘释放回调"""
        try:
            if hasattr(key, 'char'):
                char = key.char or ''
            else:
                char = str(key).replace('Key.', '')

            char = self.config.key_mapping.get(char, char)

            event_dict = {
                'event_type': 'key_release',
                'key': char,
                'modifier': self._get_modifiers(),
                'press': False,
                'timestamp': datetime.now().isoformat()
            }

            self._process_event(event_dict)

        except Exception as e:
            print(f"Error on key release: {e}")

    def _get_modifiers(self):
        """获取修饰键"""
        modifiers = []
        from pynput import keyboard as kb

        # 简单示例，实际需要从key对象判断
        return modifiers


class MouseHandler:
    """鼠标事件处理器

    使用pynput库监听鼠标输入事件。
    """

    def __init__(self, config: EventHandlerConfig):
        """初始化鼠标处理器

        Args:
            config: 事件处理器配置
        """
        self.config = config
        self._listener = None
        self._event_queue: Queue = Queue()
        self._callbacks: list[Callable] = []
        self._global_callbacks: list[Callable] = []
        self.is_running = False
        self._last_position = (0, 0)

    def register_global_callback(self, callback: Callable[[dict], None]):
        """注册全局回调函数

        Args:
            callback: 全局回调函数
        """
        self._global_callbacks.append(callback)

    def start(self):
        """启动鼠标监听"""
        if self.is_running:
            print("[Mouse Handler] Already running")
            return

        try:
            from pynput import mouse
            print("[Mouse Handler] Starting listener...")

            self._listener = mouse.Listener(
                on_move=self._on_move,
                on_click=self._on_click,
                on_scroll=self._on_scroll
            )
            self._listener.start()
            self.is_running = True
            print("✓ Mouse listener started")
        except ImportError:
            print("[ERROR] pynput library is required. Install with: pip install pynput")
            raise
        except Exception as e:
            print(f"[ERROR] Failed to start mouse listener: {e}")
            raise RuntimeError(f"Failed to start mouse listener: {e}")

    def stop(self):
        """停止鼠标监听"""
        if not self.is_running:
            return

        if self._listener:
            self._listener.stop()
            self._listener = None

        self.is_running = False
        print("Mouse listener stopped")

    def on_event(self, callback: Callable[[dict], None]):
        """注册事件回调函数

        Args:
            callback: 回调函数，接收事件字典作为参数
        """
        self._callbacks.append(callback)

    def _process_event(self, event: dict):
        """处理事件并触发回调"""
        # 特殊回调（专用）
        for callback in self._callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in event callback: {e}")

        # 全局回调
        for callback in self._global_callbacks:
            try:
                callback(event)
            except Exception as e:
                print(f"Error in mouse global callback: {e}")

    def _on_move(self, x, y):
        """pynput鼠标移动回调"""
        if not self.config.mouse_enabled:
            return

        self._last_position = (x, y)

        event_dict = {
            'event_type': 'mouse_move',
            'x': x,
            'y': y,
            'timestamp': datetime.now().isoformat()
        }

        self._process_event(event_dict)

    def _on_click(self, x, y, button, pressed):
        """pynput鼠标点击回调"""
        if not self.config.mouse_enabled:
            return

        button_name = button.name.lower()

        event_dict = {
            'event_type': 'mouse_click',
            'x': x,
            'y': y,
            'button': button_name,
            'pressed': pressed,
            'timestamp': datetime.now().isoformat()
        }

        self._process_event(event_dict)

        # 记录最后一次点击位置
        if pressed:
            self._last_position = (x, y)

    def _on_scroll(self, x, y, dx, dy):
        """pynput滚轮滚动回调"""
        if not self.config.scroll_enabled:
            return

        event_dict = {
            'event_type': 'mouse_scroll',
            'x': x,
            'y': y,
            'delta_x': dx,
            'delta_y': dy,
            'timestamp': datetime.now().isoformat()
        }

        self._process_event(event_dict)


class EventHandler:
    """统一的事件处理器

    整合键盘和鼠标处理器，提供统一的管理接口。
    """

    def __init__(self, config: EventHandlerConfig = None):
        """初始化事件处理器

        Args:
            config: 事件处理器配置
        """
        if config is None:
            config = EventHandlerConfig()

        self.config = config
        self.keyboard_handler = KeyboardHandler(config)
        self.mouse_handler = MouseHandler(config)
        self._global_callbacks: list[Callable[[dict], None]] = []

    def register_global_callback(self, callback: Callable[[dict], None]):
        """注册全局回调函数
        此回调会被 EventHandler 及其子处理器调用

        Args:
            callback: 全局回调函数
        """
        self._global_callbacks.append(callback)

        # 也注册到两个处理器
        self.keyboard_handler.register_global_callback(callback)
        self.mouse_handler.register_global_callback(callback)

    def start(self):
        """启动所有监听器"""
        if self.config.keyboard_enabled:
            self.keyboard_handler.start()

        if self.config.mouse_enabled:
            self.mouse_handler.start()

    def stop(self):
        """停止所有监听器"""
        if self.config.keyboard_enabled:
            self.keyboard_handler.stop()

        if self.config.mouse_enabled:
            self.mouse_handler.stop()

    def is_running(self):
        """检查是否正在运行"""
        return self.keyboard_handler.is_running or self.mouse_handler.is_running

    def get_last_mouse_position(self):
        """获取最后记录的鼠标位置"""
        return self.mouse_handler._last_position


from datetime import datetime
