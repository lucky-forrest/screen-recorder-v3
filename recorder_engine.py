"""操作录制引擎

核心录制引擎，协调事件采集、数据导出。
"""
import json
import threading
import time
import os
import shutil
from pathlib import Path
from queue import Queue, Empty
from typing import Optional, List, Callable
from collections import deque
from datetime import datetime

from data.event import OperationEvent, EventType, SessionStartEvent, SessionEndEvent, WindowSpecificInfo, UIElementInfo
from event_handler import EventHandler, EventHandlerConfig
from element_detector.base_detector import BaseUIDetector
from element_detector.textbox_detector import TextBoxDetector
from element_detector.button_detector import ButtonDetector
from element_detector.dropdown_detector import DropdownDetector
import utils.config_loader as config_loader
import utils.timestamp_manager as timestamp_manager
import utils.path_manager as path_manager
from utils.file_manager import FileManager


class RecorderEngine:
    """操作录制引擎

    协调键盘鼠标监听、UI元素识别和数据导出。
    """

    def __init__(self, config_path: str = "config.json"):
        """初始化录制引擎

        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        self.config = config_loader.load_config(config_path)
        self.path_manager = path_manager.PathManager(config_path)

        # 录制状态
        self.is_recording = False
        self.session_id = None
        self.current_session = None
        self.is_paused = False  # 新增：暂停状态
        self._pause_event = threading.Event()  # 新增：暂停标志位

        # 事件队列
        self.event_queue: Queue = Queue(maxsize=self.config["recording"]["event_queue_size"])
        self.session_events: deque = deque(maxlen=10000)

        # UI元素检测器
        self.textbox_detector = TextBoxDetector(
            confidence_threshold=self.config["ui_detection"]["confidence_threshold"]
        )
        self.button_detector = ButtonDetector(
            confidence_threshold=self.config["ui_detection"]["confidence_threshold"]
        )
        self.dropdown_detector = DropdownDetector(
            confidence_threshold=self.config["ui_detection"]["confidence_threshold"]
        )

        # 视频生成器（可选）
        self.video_generator = None

        # 回调函数
        self._event_callback: Optional[Callable] = None
        self._status_callback: Optional[Callable] = None

        # 线程锁
        self._lock = threading.Lock()

    def start_recording(self) -> str:
        """开始录制

        Returns:
            str: session_id
        """
        if self.is_recording:
            raise RuntimeError("Already recording")

        # 重置暂停状态
        self.is_paused = False
        self._pause_event.clear()

        # 生成session_id
        self.session_id = timestamp_manager.generate_session_id()
        self.current_session = SessionStartEvent(self.session_id)

        # 初始化事件队列为空
        self.session_events.clear()

    
        # 启动视频生成器（如果可用）
        if self.video_generator is not None:
            self.video_generator.start_generating(self.session_id)

        # 启动事件处理器
        event_config = EventHandlerConfig(
            keyboard_enabled=self.config["ui_detection"].get("enabled", True),
            mouse_enabled=self.config["ui_detection"].get("enabled", True)
        )

        self.event_handler = EventHandler(event_config)

        # 注册全局回调
        self.event_handler.register_global_callback(self._process_raw_event)

        # 启动事件处理器
        self.event_handler.start()

        # 更新录制状态
        self.is_recording = True

        if self._status_callback:
            self._status_callback("recording_started", {"session_id": self.session_id})

        print(f"Recording started: {self.session_id}")
        return self.session_id

    def stop_recording(self, message_name: str = None) -> List[OperationEvent]:
        """停止录制

        Args:
            message_name: 可选的消息名称，用于创建对应文件夹

        Returns:
            List[OperationEvent]: 录制的事件列表
        """
        if not self.is_recording:
            raise RuntimeError("Not recording")

        # 停止事件处理器
        if hasattr(self, 'event_handler'):
            self.event_handler.stop()

        # 捕获结束事件
        self.current_session = SessionEndEvent(self.session_id, len(self.session_events))

        # 更新录制状态
        self.is_recording = False

        if self._status_callback:
            self._status_callback("recording_stopped", {
                "session_id": self.session_id,
                "event_count": len(self.session_events)
            })

        print(f"Recording stopped: {self.session_id}, events: {len(self.session_events)}")

        # 如果提供了消息名称，使用消息名称文件夹保存文件
        if message_name:
            message_name = FileManager.sanitize_filename(message_name)
            self.save_to_csv_with_message_name(message_name)
            self.save_to_json_with_message_name(message_name)
            # 视频文件需要手动重命名
            self._rename_video_file(message_name)
        else:
            print("未提供消息名称，跳过文件导出")

        # 返回所有事件
        return list(self.session_events)


    def save_to_csv_with_message_name(self, message_name: str) -> Optional[str]:
        """保存为CSV格式（使用消息名称作为文件夹）

        Args:
            message_name: 录制消息名称

        Returns:
            Optional[str]: 保存的文件路径，失败返回None
        """
        if not self.session_events:
            print("No events to save")
            return None

        filepath = self.path_manager.get_message_csv_file_path(message_name)

        # 创建目录
        try:
            msg_dir = self.path_manager.get_message_directory(message_name)
            msg_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"✗ 创建消息目录失败: {e}")
            return None

        # 写入CSV
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                f.write("timestamp,event_type,detail,x,y,window_title,element_type,element_content,window_handle,window_class_name,window_process_id,control_handle,control_class_name,control_text\n")

                for event in self.session_events:
                    try:
                        export_data = event.get_export_dict()
                        # 处理None值
                        window_title = export_data.get('window_title') or ''
                        element_type = export_data.get('element_type') or ''
                        element_content = export_data.get('element_content') or ''

                        line = (
                            f"{export_data['time']},"
                            f"{export_data['type']},"
                            f"{export_data['detail']},"
                            f"{export_data['x']},{export_data['y']},"
                            f"{window_title},"
                            f"{element_type},"
                            f"{element_content}\n"
                        )
                        f.write(line)
                    except (IOError, OSError) as e:
                        print(f"Error writing event to CSV: {e}")

            print(f"✓ CSV文件已保存: {filepath}")
            return str(filepath)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"✗ 保存CSV失败: {e}")
            return None


    def save_to_json_with_message_name(self, message_name: str) -> Optional[str]:
        """保存为JSON格式（使用消息名称作为文件夹）

        Args:
            message_name: 录制消息名称

        Returns:
            Optional[str]: 保存的文件路径，失败返回None
        """
        if not self.session_events:
            print("No events to save")
            return None

        filepath = self.path_manager.get_message_json_file_path(message_name)

        # 创建目录
        try:
            msg_dir = self.path_manager.get_message_directory(message_name)
            msg_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            print(f"✗ 创建消息目录失败: {e}")
            return None

        # 构建JSON数据
        try:
            # 获取开始时间
            if isinstance(self.current_session, SessionStartEvent):
                start_time = self.current_session.start_time.isoformat()
            elif isinstance(self.current_session, SessionEndEvent):
                # 如果是SessionEndEvent，尝试从session_events获取第一个事件的时间
                start_time = self.session_events[0].timestamp.isoformat() if self.session_events else datetime.now().isoformat()
                # 更新current_session为开始时间
                self.current_session.start_time = datetime.fromisoformat(start_time)
            else:
                start_time = self.current_session.start_time.isoformat() if hasattr(self.current_session, 'start_time') else datetime.now().isoformat()

            json_data = {
                "session_id": self.session_id,
                "start_time": start_time,
                "event_count": len(self.session_events),
                "events": [event.get_full_json() for event in self.session_events]
            }

            # 写入JSON
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(json_data, f, indent=2, ensure_ascii=False)

            print(f"✓ JSON文件已保存: {filepath}")
            return str(filepath)
        except (IOError, OSError, json.JSONDecodeError) as e:
            print(f"✗ 保存JSON失败: {e}")
            return None

    def get_session_events(self) -> List[OperationEvent]:
        """获取当前会话的事件列表

        Returns:
            List[OperationEvent]: 事件列表
        """
        with self._lock:
            return list(self.session_events)

    def save_video_to_message_directory(
        self,
        message_name: str,
        source_video_path: Optional[str] = None,
        overwrite: bool = False
    ) -> Optional[str]:
        """Save the finalized session video into the message subdirectory."""
        try:
            if self.video_generator is not None:
                self.video_generator.wait_until_complete(timeout=20.0)

            sanitized_name = FileManager.sanitize_filename(message_name)
            original_video_path = Path(source_video_path) if source_video_path else self.path_manager.get_video_file_path(self.session_id)
            if not original_video_path.exists():
                print(f"⚠ 视频文件不存在: {original_video_path}")
                return None

            message_dir = self.path_manager.get_message_directory(sanitized_name)
            message_dir.mkdir(parents=True, exist_ok=True)
            target_video_path = message_dir / f"{sanitized_name}_operation_video.mp4"

            if target_video_path.exists() and not overwrite:
                print(f"⚠ 目标视频文件已存在，跳过复制: {target_video_path}")
                return str(target_video_path)

            shutil.copy2(str(original_video_path), str(target_video_path))
            print(f"✓ 视频文件已复制到: {target_video_path}")
            return str(target_video_path)

        except Exception as e:
            print(f"✗ 保存子目录视频文件失败: {e}")
            return None

    def _rename_video_file(self, message_name: str):
        """兼容旧调用，保留原方法名。"""
        self.save_video_to_message_directory(message_name)

    def on_event(self, callback: Callable[[OperationEvent], None]):
        """注册事件回调

        Args:
            callback: 回调函数
        """
        self._event_callback = callback

    def _trigger_callbacks(self, event: OperationEvent):
        """触发所有注册的事件回调

        Args:
            event: 操作事件
        """
        print(f"[RecorderEngine] Event triggered: {event.event_type.value} - {event.detail}")
        if self._event_callback:
            try:
                self._event_callback(event)
            except (TypeError, AttributeError) as e:
                print(f"[RecorderEngine] Error in event callback: {e}")

    def on_status(self, callback: Callable[[str, dict], None]):
        """注册状态回调

        Args:
            callback: 回调函数 (status_type, status_data)
        """
        self._status_callback = callback

    def _trigger_status_callback(self, status_type: str, status_data: dict):
        """触发状态回调

        Args:
            status_type: 状态类型
            status_data: 状态数据
        """
        if self._status_callback:
            try:
                self._status_callback(status_type, status_data)
            except (TypeError, AttributeError):
                pass

    def _process_raw_event(self, event_data: dict):
        """处理原始事件数据

        Args:
            event_data: 原始事件字典
        """
        if not self.is_recording:
            return

        # 新增：如果暂停，直接丢弃事件
        if self.is_paused:
            return

        event_type = event_data.get("event_type")
        x = event_data.get("x", 0)
        y = event_data.get("y", 0)

        try:
            # 创建操作事件
            op_event = None

            if event_type == "key_press" or event_type == "key_release":
                op_event = self._create_operation_event_from_keyboard(event_data)
            elif event_type == "mouse_click":
                op_event = self._create_operation_event_from_mouse(event_data)
            elif event_type == "mouse_move":
                # 鼠标移动时也添加事件用于捕捉窗口信息
                op_event = OperationEvent(
                    event_type=EventType.MOUSE_MOVE,
                    detail=f"Mouse at ({x}, {y})",
                    coordinates=(x, y)
                )

            if op_event:
                # 为鼠标事件获取窗口信息
                if event_type == "mouse_click" or event_type == "mouse_move":
                    window_info = self._get_window_info_at_position(x, y)
                    op_event.window_info = window_info

                self.session_events.append(op_event)
                # 发送到视频生成器
                try:
                    if hasattr(self, 'video_generator') and self.video_generator._is_generating:
                        self.video_generator.add_event(op_event)
                except Exception as ve:
                    print(f"[RecorderEngine] Video generator error: {ve}")


            else:
                pass  # 忽略未知事件类型


        except Exception as e:
            print(f"Error processing event: {e}")
            import traceback
            traceback.print_exc()

    def _create_operation_event_from_keyboard(self, event_data: dict, element_info: UIElementInfo = None) -> Optional[OperationEvent]:
        """从键盘事件创建操作事件

        Args:
            event_data: 键盘事件字典
            element_info: UI元素信息（如果有）

        Returns:
            Optional[OperationEvent]: 操作事件，或None
        """
        key = event_data.get("key", "")
        modifier = event_data.get("modifier", [])
        event_type_in = event_data["event_type"]  # "key_press" or "key_release"

        # 只记录按键事件，不记录释放事件（除非特殊需要）
        if event_type_in == "key_release" and key not in ("Enter", "Space", "Tab", "Escape"):
            return None

        display_key = key
        if modifier:
            mods = " + ".join(modifier)
            display_key = f"{mods} + {key}" if key else mods

        op_event = OperationEvent(
            event_type=EventType.KEY_PRESS,
            detail=f"Key: {display_key}",
            coordinates=(0, 0),  # 键盘事件没有坐标
            element_info=element_info if hasattr(element_info, 'confidence') and element_info.confidence > 0 else None
        )

        return op_event

    def _create_operation_event_from_mouse(self, event_data: dict, element_info: UIElementInfo = None) -> Optional[OperationEvent]:
        """从鼠标事件创建操作事件

        Args:
            event_data: 鼠标事件字典
            element_info: UI元素信息（如果有）

        Returns:
            Optional[OperationEvent]: 操作事件，或None
        """
        button = event_data.get("button", "left")
        pressed = event_data.get("pressed", True)

        # 只记录点击（按下）事件，不记录释放
        if not pressed:
            return None

        display_detail = f"Mouse {button} Click"

        op_event = OperationEvent(
            event_type=EventType.MOUSE_CLICK,
            detail=display_detail,
            coordinates=(event_data.get("x", 0), event_data.get("y", 0)),
            element_info=element_info if element_info and element_info.confidence > 0 else None
        )

        return op_event
    def pause_recording(self):
        """暂停录制"""
        if not self.is_recording:
            raise RuntimeError("Not recording")

        self.is_paused = True
        print("✓ 录制已暂停")

    def resume_recording(self):
        """恢复录制"""
        if not self.is_recording:
            raise RuntimeError("Not recording")
        if not self.is_paused:
            raise RuntimeError("Not paused")

        self.is_paused = False
        print("✓ 录制已恢复")

    def _get_window_info_at_position(self, x: int, y: int) -> Optional[WindowSpecificInfo]:
        """获取指定位置的窗口信息

        Args:
            x: X坐标
            y: Y坐标

        Returns:
            Optional[WindowSpecificInfo]: 窗口特定信息
        """
        try:
            from window_info_monitor import get_monitor

            monitor = get_monitor()
            window_info = monitor.get_current_window_info()

            # 获取控件信息
            control_info = monitor.get_hovered_control_info()

            # 创建窗口特定信息
            window_specific_info = WindowSpecificInfo(
                window_handle=window_info.handle,
                window_title=window_info.title,
                window_class_name=window_info.class_name,
                window_process_id=window_info.process_id,
                window_process_name=window_info.process_name,
                control_handle=control_info.handle if control_info else 0,
                control_class_name=control_info.class_name if control_info else "",
                control_text=control_info.text if control_info else ""
            )

            return window_specific_info

        except Exception as e:
            print(f"获取窗口信息失败: {e}")
            return None

