"""文本框检测器

识别文本框、输入框等文本输入元素。
"""
import cv2
import numpy as np
from typing import Optional
from data.event import UIElementType
from .base_detector import BaseUIDetector


class TextBoxDetector(BaseUIDetector):
    """文本框检测器"""

    # 文本框特征模式：矩形有边框、内边距、可能有填充
    def __init__(self, confidence_threshold: float = 0.6):
        """初始化文本框检测器

        Args:
            confidence_threshold: 置信度阈值
        """
        super().__init__(confidence_threshold)
        self._text_box_patterns = []

    def detect(self, region: np.ndarray, mouse_pos: tuple) -> UIElementType:
        """检测鼠标位置附近的文本框

        Args:
            region: 屏幕区域图像
            mouse_pos: 鼠标位置 (x, y)

        Returns:
            UIElementType: 检测到的元素类型
        """
        # 1. 计算图像对比度（文本框通常有背景差异）
        if not self._is_valid_image(region):
            return UIElementType.OTHER

        contrast = self._calculate_contrast(region)

        # 2. 检测边缘密度（文本框通常有明显的边框）
        edge_density = self.calculate_edge_density(region)

        # 3. 计算颜色变异性（文本框内部可能有变化）
        color_variance = self._calculate_color_variance(region)

        # 特征评分（需要根据实际情况调整权重）
        features = {
            "edge_density": edge_density * 0.5,      # 边缘是强特征
            "contrasts": contrast * 10.0,            # 对比度倍数增强
            "color_variance": color_variance * 0.3
        }

        total_score = sum(features.values())
        confidence = min(total_score / 2.0, 1.0)

        # 判断是否是文本框
        is_text_box = (
            edge_density > 0.02 and
            contrast > 0.1 and
            confidence >= self.confidence_threshold
        )

        if is_text_box:
            # 提取文本内容
            text = self.get_text_content(region)
            return UIElementInfo(
                element_type=UIElementType.TEXTBOX,
                element_content=text,
                bounding_box=self.detect_element_bounds(region, mouse_pos),
                confidence=confidence,
                state={"has_border": edge_density > 0.05, "has_text": text is not None}
            )

        return UIElementInfo(
            element_type=UIElementType.OTHER,
            confidence=confidence
        )

    def _calculate_contrast(self, image: np.ndarray) -> float:
        """计算图像平均对比度

        Args:
            image: 图像

        Returns:
            float: 对比度值
        """
        if len(image.shape) == 2:  # 灰度图
            gray = image
        else:  # 彩色图
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # 计算局部对比度（使用简单的差异计算）
        if gray.shape[0] > 2 and gray.shape[1] > 2:
            diff_x = np.abs(np.diff(gray, axis=1))
            diff_y = np.abs(np.diff(gray, axis=0))
            contrast = (np.mean(diff_x) + np.mean(diff_y)) / 255.0
            return np.clip(contrast, 0, 1)
        return 0.0

    def _calculate_color_variance(self, image: np.ndarray) -> float:
        """计算颜色的方差

        Args:
            image: 图像

        Returns:
            float: 颜色方差
        """
        if len(image.shape) == 2:  # 灰度图
            return float(np.mean(np.std(image)))

        # 计算亮度方差
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return float(np.mean(np.std(gray)))

    def _is_valid_image(self, image: np.ndarray) -> bool:
        """检查是否是有效的图像

        Args:
            image: 图像

        Returns:
            bool: 是否有效
        """
        if image is None or image.size == 0:
            return False

        # 检查图像尺寸
        h, w = image.shape[:2]
        if w < 5 or h < 5:
            return False

        return True
