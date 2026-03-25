"""UI元素分析器

实时分析屏幕UI元素，提供元素类型和内容的识别。
"""
import time
import threading
from typing import Optional
from data.event import OperationEvent, UIElementInfo, UIElementType
import cv2
import numpy as np


class UIAnalyzer:
    """UI元素分析器

    实时分析鼠标位置及其周围的UI元素。
    """

    def __init__(self, recorder_engine=None):
        """初始化UI分析器

        Args:
            recorder_engine: 录制引擎实例
        """
        self.recorder_engine = recorder_engine

        # 当前状态
        self.current_window_title: Optional[str] = None
        self.last_analysis_time = 0
        self.analysis_interval = 0.1  # 100ms分析频率

        # 元素缓存
        self.element_cache: dict = {}

        # 分析线程
        self._analysis_thread: Optional[threading.Thread] = None
        self._analyzer_running = False

    def start(self):
        """启动UI分析器"""
        if self._analyzer_running:
            return

        self._analyzer_running = True
        self._analysis_thread = threading.Thread(target=self._analysis_loop, daemon=True)
        self._analysis_thread.start()
        print("UI analyzer started")

    def stop(self):
        """停止UI分析器"""
        self._analyzer_running = False
        if self._analysis_thread:
            self._analysis_thread.join(timeout=1.0)
        print("UI analyzer stopped")

    def update_window_title(self, title: str):
        """更新当前窗口标题

        Args:
            title: 窗口标题
        """
        self.current_window_title = title

    def analyze_at_position(self, x: int, y: int, force: bool = False):
        """分析指定位置的元素

        Args:
            x: X坐标
            y: Y坐标
            force: 是否强制分析
        """

        current_time = time.time()

        # 检查是否需要分析（频率限制或强制）
        if not force and current_time - self.last_analysis_time < self.analysis_interval:
            return

        try:
            # 截取当前屏幕
            from pyautogui import screenshot
            screen = screenshot()

            # 转换为OpenCV格式
            import numpy as np
            screen_rgb = np.array(screen)
            screen_cv = cv2.cvtColor(screen_rgb, cv2.COLOR_RGB2BGR)

            # 分析该位置的元素
            element_info = self._analyze_screen_region(screen_cv, (x, y))

            if element_info:
                self.element_cache[(x, y)] = element_info
                self.last_analysis_time = current_time

                # 如果正在录制，发送UI交互事件
                if self.recorder_engine and self.recorder_engine.is_recording:
                    self.recorder_engine._process_ui_interaction(x, y)

        except Exception as e:
            print(f"Error analyzing UI: {e}")

    def _analyze_screen_region(self, screen, region_center):
        """分析屏幕区域

        Args:
            screen: 屏幕图像
            region_center: 区域中心坐标

        Returns:
            Optional[UIElementInfo]: 元素信息，或None
        """
        # 创建检测器实例
        textbox_detector = self.recorder_engine.textbox_detector if self.recorder_engine else None
        button_detector = self.recorder_engine.button_detector if self.recorder_engine else None
        dropdown_detector = self.recorder_engine.dropdown_detector if self.recorder_engine else None

        if textbox_detector is None or button_detector is None or dropdown_detector is None:
            return None

        # 分析文本框
        textbox_result = textbox_detector.detect(screen, region_center)
        element_info = textbox_result

        # 如果文本框置信度高，优先返回
        if textbox_result.confidence >= textbox_detector.confidence_threshold:
            return textbox_result

        # 尝试按钮检测
        button_result = button_detector.detect(screen, region_center)
        if button_result and button_result.confidence >= button_detector.confidence_threshold:
            element_info = button_result

        # 尝试下拉框检测
        if dropdown_detector:
            dropdown_result = dropdown_detector.detect(screen, region_center)
            if dropdown_result and dropdown_result.confidence >= dropdown_detector.confidence_threshold:
                element_info = dropdown_result

        return element_info if element_info.confidence > 0 else None

    def _analysis_loop(self):
        """分析循环"""
        while self._analyzer_running:
            # 简单实现：每秒检查一次鼠标位置
            try:
                from pyautogui import position
                if self.recorder_engine and self.recorder_engine.is_recording:
                    mouse_pos = position()
                    self.analyze_at_position(mouse_pos[0], mouse_pos[1], force=True)
            except Exception:
                pass

            # 控制频率
            time.sleep(self.analysis_interval)
