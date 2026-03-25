"""按钮检测器

识别按钮、点击项等交互元素。
"""
import cv2
import numpy as np
from typing import Optional
from data.event import UIElementType
from .base_detector import BaseUIDetector


class ButtonDetector(BaseUIDetector):
    """按钮检测器"""

    def __init__(self, confidence_threshold: float = 0.6):
        """初始化按钮检测器

        Args:
            confidence_threshold: 置信度阈值
        """
        super().__init__(confidence_threshold)
        self._button_templates = {}

    def detect(self, region: np.ndarray, mouse_pos: tuple) -> Optional[UIElementType]:
        """检测常用的UI模式（边框、文本、填充等）

        Args:
            region: 屏幕区域图像
            mouse_pos: 鼠标位置 (x, y)

        Returns:
            Optional[UIElementType]: 文本框元素信息，或None
        """
        if not self._is_valid_image(region):
            return None

        # 1. 检测矩形/斜切元素的轮廓
        edge_density = self.calculate_edge_density(region)

        # 2. 计算颜色变化（按钮可能有纯色背景）
        is_solid_color = self._is_mostly_solid_color(region)

        # 3. 计算区域紧凑度（按钮通常有合理的宽高比）
        compactness = self._calculate_compactness(region)

        # 特征评分
        features = {
            "edge_density": edge_density * 0.5,
            "is_solid_color": (0.5 if is_solid_color else 0.0),
            "compactness": compactness * 0.3
        }

        total_score = sum(features.values())
        confidence = min(total_score / 1.5, 1.0)

        if confidence >= self.confidence_threshold:
            # 按钮通常没有边框（或者边框很细），但会有明显的文本和颜色
            return UIElementInfo(
                element_type=UIElementType.BUTTON,
                element_content=self.get_text_content(region),
                bounding_box=self.detect_element_bounds(region, mouse_pos),
                confidence=confidence,
                state={
                    "solid_background": is_solid_color,
                    "compact_shape": compactness > 0.1
                }
            )

        return None

    def _is_mostly_solid_color(self, image: np.ndarray) -> bool:
        """判断图像是否主要是单色

        Args:
            image: 图像

        Returns:
            bool: 是否主要是单色
        """
        h, w = image.shape[:2]

        # 转为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 计算像素方差
        if gray.shape[0] < 2 or gray.shape[1] < 2:
            return False

        pixel_variance = np.var(gray)

        # 如果方差小于阈值，认为是纯色区域
        return pixel_variance < 20.0

    def _calculate_compactness(self, image: np.ndarray) -> float:
        """计算区域紧凑度（面积与边界框的比率）

        Args:
            image: 图像

        Returns:
            float: 紧凑度值 (0-1)
        """
        h, w = image.shape[:2]

        # 计算面积与最小外接矩形的比率
        if w < 5 or h < 5:
            return 0.0

        area = h * w
        min_size = min(w, h)
        compactness = min_size / max(w, h)

        return np.clip(compactness, 0, 1)

    def _is_valid_image(self, image: np.ndarray) -> bool:
        """检查是否是有效的图像

        Args:
            image: 图像

        Returns:
            bool: 是否有效
        """
        if image is None or image.size == 0:
            return False

        h, w = image.shape[:2]
        if w < 5 or h < 5:
            return False

        return True
