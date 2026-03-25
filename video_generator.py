"""视频生成器

生成操作视频，回放用户操作流程。
"""
import cv2
import numpy as np
import threading
from queue import Queue
from typing import Optional
from datetime import datetime
from pathlib import Path
from data.event import OperationEvent
import utils.timestamp_manager as timestamp_manager
import utils.path_manager as path_manager


class VideoGenerator:
    """视频生成器

    将录制的操作序列生成视频文件，支持轨迹叠加和标签显示。
    """

    def __init__(self, config_path: str = "config.json"):
        """初始化视频生成器

        Args:
            config_path: 配置文件路径
        """
        # 使用PathManager管理路径
        self.path_manager = path_manager.PathManager(config_path)
        self.config = self.path_manager.config

        # 视频配置
        self.fps = self.config.get("video", {}).get("framerate", 30)
        self.quality = self.config.get("video", {}).get("output_quality", 85)

        # 线程安全的队列
        self.event_queue: Queue = Queue()
        self._generator_thread: Optional[threading.Thread] = None
        self._is_generating = False
        self.current_video_writer: Optional[cv2.VideoWriter] = None
        self.video_path: Optional[str] = None

    def start_generating(self, session_id: str):
        """开始生成视频

        Args:
            session_id: 会话ID
        """
        if self._is_generating:
            print("Video already generating, skipping")
            return

        self._is_generating = True
        self.video_path = self._get_video_path(session_id)

        # 创建输出视频文件
        try:
            self._init_video_writer()
        except Exception as e:
            print(f"⚠ 视频初始化失败: {e}")
            print("继续运行，但不生成视频...")
            self._is_generating = False
            return

        # 启动生成线程
        self._generator_thread = threading.Thread(
            target=self._generation_loop,
            daemon=True
        )
        self._generator_thread.start()

        print(f"✓ Video generation started: {self.video_path}")

    def add_event(self, event: OperationEvent):
        """添加操作事件

        Args:
            event: 操作事件
        """
        if self._is_generating:
            self.event_queue.put(event)

    def stop_generating(self, wait: bool = True):
        """停止视频生成

        Args:
            wait: 是否等待线程结束
        """
        if not self._is_generating:
            print("✗ 视频生成未启动，跳过")
            return

        self._is_generating = False

        # 发送结束信号
        if hasattr(self, 'event_queue'):
            self.event_queue.put(None)

        if wait and self._generator_thread:
            self._generator_thread.join(timeout=5.0)

        print("✓ 视频生成停止")

    def get_video_path(self) -> Optional[str]:
        """获取视频文件路径

        Returns:
            Optional[str]: 视频文件路径，如果未生成则返回None
        """
        if hasattr(self, 'video_path') and self.video_path:
            return str(self.video_path)
        return None

    def _set_resolution(self):
        """设置视频分辨率"""
        from pyautogui import size
        screen_width, screen_height = size()
        return (screen_width, screen_height)

    def _init_video_writer(self):
        """初始化视频写入器"""
        resolution = self._set_resolution()
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.current_video_writer = cv2.VideoWriter(
            self.video_path,
            fourcc,
            self.fps,
            resolution
        )

        # 添加时间戳水印
        self._timestamp_font = cv2.FONT_HERSHEY_SIMPLEX
        self._timestamp_scale = 1
        self._timestamp_thickness = 2
        self._timestamp_color = (0, 255, 0)

    def _get_video_path(self, session_id: str) -> Path:
        """获取视频文件路径

        Args:
            session_id: 会话ID

        Returns:
            Path: 视频文件路径
        """
        return self.path_manager.get_video_file_path(session_id)

    def _generate_frame(self, event: OperationEvent) -> Optional[cv2.Mat]:
        """生成视频帧

        Args:
            event: 操作事件

        Returns:
            Optional[cv2.Mat]: 视频帧图像，或None
        """
        try:
            # 截图当前屏幕
            from pyautogui import screenshot
            frame = np.array(screenshot())

            # 转换颜色空间
            frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            # 验证图像大小
            if frame_bgr is None or frame_bgr.size == 0:
                return None

            # 绘制操作轨迹线
            if event.event_type.value == "mouse_click":
                # 添加点击标记（十字光标）
                x, y = event.coordinates
                cv2.drawMarker(
                    frame_bgr,
                    (x, y),
                    (0, 255, 0),
                    markerType=cv2.MARKER_CROSS,
                    markerSize=20,
                    thickness=2
                )

            # 绘制操作标签
            label = self._get_event_label(event)

            # 添加透明背景矩形
            text_size = cv2.getTextSize(
                label,
                self._timestamp_font,
                self._timestamp_scale,
                self._timestamp_thickness
            )[0]

            bg_y = 20
            bg_x = 10

            # 绘制背景
            cv2.rectangle(
                frame_bgr,
                (bg_x - 5, bg_y - text_size[1] - 5, bg_x + text_size[0] + 5, bg_y + 10),
                (0, 0, 0),
                cv2.FILLED
            )

            # 绘制文字
            cv2.putText(
                frame_bgr,
                label,
                (bg_x, bg_y),
                self._timestamp_font,
                self._timestamp_scale,
                self._timestamp_color,
                self._timestamp_thickness
            )

            # 添加时间戳
            timestamp_text = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")
            cv2.putText(
                frame_bgr,
                timestamp_text,
                (10, frame_bgr.shape[0] - 15),
                self._timestamp_font,
                0.7,
                (255, 255, 255),
                1
            )

            return frame_bgr

        except Exception as e:
            print(f"Error generating frame: {e}")
            return None

    def _get_event_label(self, event: OperationEvent) -> str:
        """获取事件标签字符串

        Args:
            event: 操作事件

        Returns:
            str: 标签字符串
        """
        event_type = event.event_type.value
        detail = event.detail

        # 附加UI元素信息
        if event.element_info:
            element_type = event.element_info.element_type.value
            content = event.element_info.element_content or ""
            if len(content) > 20:
                content = content[:20] + "..."
            return f"{event_type} [{element_type}] {detail}: {content}"
        else:
            return f"{event_type} {detail}"

    def _generation_loop(self):
        """生成循环"""
        import time
        frame_count = 0
        last_event = None
        frame_delay = 0.05  # 50ms间隔

        print("[Video Generator] Loop started")
        print("[Video Generator] Waiting for events...")
        time.sleep(1)  # 给1秒时间让事件进来

        while self._is_generating or not self.event_queue.empty():
            try:
                # 从队列获取事件
                event = self.event_queue.get(timeout=0.1)

                if event is None:
                    # 结束信号，等待队列清空
                    if self.event_queue.empty():
                        frame_count += 1  # 确保最后一帧被捕获
                        break
                    continue

                # 生成帧
                frame = self._generate_frame(event)

                if frame is not None and self.current_video_writer is not None:
                    self.current_video_writer.write(frame)
                    frame_count += 1

                # 控制帧率
                if frame_count % self.fps == 0:
                    time.sleep(1 / self.fps)

            except Exception as e:
                print(f"[Video Generator] Error during generation: {e}")
                break

        # 停止视频写入器
        try:
            if self.current_video_writer:
                self.current_video_writer.release()
        except:
            pass
        self.current_video_writer = None

        print(f"✓ Video generated: {frame_count} frames at {self.video_path}")
