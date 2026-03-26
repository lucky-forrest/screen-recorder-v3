"""下拉框检测器

识别下拉框、选择器等展开/收起控件。
"""
import cv2
import numpy as np
from typing import Optional
from data.event import UIElementType
from .base_detector import BaseUIDetector


class DropdownDetector(BaseUIDetector):
    """下拉框检测器"""

    def __init__(self, confidence_threshold: float = 0.65):
        """初始化下拉框检测器

        Args:
            confidence_threshold: 置信度阈值
        """
        super().__init__(confidence_threshold)
        self._arrow_marker = self._create_arrow_marker()

    def detect(self, region: np.ndarray, mouse_pos: tuple) -> Optional[UIElementType]:
        """检测下拉框/下拉菜单

        Args:
            region: 屏幕区域图像
            mouse_pos: 鼠标位置 (x, y)

        Returns:
            Optional[UIElementType]: 下拉框元素信息，或None
        """
        if not self._is_valid_image(region):
            return None

        # 下拉框特征：
        # 1. 有可见的箭头标记（通常在右侧）
        # 2. 有明显的选中项文本
        # 3. 边框略粗糙（与普通文本框不同）

        # 检测箭头
        arrow_detected = self._detect_arrow(region)

        # 提取默认文本
        text = self.get_text_content(region)
        content = text.split('\n')[0] if text else None

        features = {
            "has_arrow": 0.5 if arrow_detected else 0.0,
            "has_text": (0.5 if content else 0.0)
        }

        total_score = sum(features.values())
        confidence = min(total_score / 1.0, 1.0)

        if confidence >= self.confidence_threshold:
            return UIElementInfo(
                element_type=UIElementType.DROPDOWN,
                element_content=content,
                bounding_box=self.detect_element_bounds(region, mouse_pos),
                confidence=confidence,
                state={
                    "has_arrow": arrow_detected,
                    "has_expansion_marker": content is not None
                }
            )

        return None

    def _detect_arrow(self, image: np.ndarray) -> bool:
        """检测下拉箭头

        Args:
            image: 图像

        Returns:
            bool: 是否检测到箭头
        """
        # 方法1：使用模板匹配（如果有箭头）
        template = self._arrow_marker

        if template is None:
            # 方法2：使用图像梯度分析
            return self._analyze_gradient_patterns(image)
        else:
            # 方法3：模板匹配
            result = cv2.matchTemplate(image, template, cv2.TM_CCOEFF_NORMED)
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
            return max_val > 0.6

    def _create_arrow_marker(self):
        """创建下拉箭头符号模板

        Returns:
            np.ndarray: 箭头模板图像
        """
        try:
            # 创建简单的向下箭头符号
            arrow = np.zeros((20, 20, 1), dtype=np.uint8)

            # 箭头形状
            cv2.line(arrow, (9, 0), (9, 15), 255, 2)
            cv2.line(arrow, (5, 12), (9, 8), 255, 2)
            cv2.line(arrow, (13, 12), (9, 8), 255, 2)

            return arrow
        except (cv2.error, TypeError, ValueError) as e:
            return None

    def _analyze_gradient_patterns(self, image: np.ndarray) -> bool:
        """分析梯度模式寻找箭头

        Args:
            image: 图像

        Returns:
            bool: 是否有箭头模式
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape

        # 创建水平梯度
        grad_x = np.abs(np.diff(gray, axis=1)).astype(np.float32)

        # 检查右侧是否有垂直线条（箭头形状）
        c = int(w * 0.7)  # 右侧区域
        right_edge_sum = grad_x[c:, min(c+10, w-1)]

        # 箭头在垂直方向有下降趋势
        right_edge_variance = np.var(right_edge_sum)
        has_arrow_variance = right_edge_variance > right_edge_sum.mean() * 0.8

        return has_arrow_variance

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
