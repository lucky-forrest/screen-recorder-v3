"""UI元素检测器基类

定义UI元素检测器的抽象接口和通用功能。
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, Tuple
from data.event import UIElementType, UIElementInfo
import cv2
import numpy as np


class BaseUIDetector(ABC):
    """UI元素检测器抽象基类"""

    def __init__(self, confidence_threshold: float = 0.7):
        """初始化检测器

        Args:
            confidence_threshold: 置信度阈值
        """
        self.confidence_threshold = confidence_threshold
        self._element_cache: Dict[Tuple[int, int], UIElementInfo] = {}

    @abstractmethod
    def detect(self, screen: np.ndarray, mouse_pos: Tuple[int, int]) -> UIElementInfo:
        """检测UI元素

        Args:
            screen: 当前屏幕图像
            mouse_pos: 鼠标位置 (x, y)

        Returns:
            UIElementInfo: 检测到的元素信息

        Raises:
            NotImplementedError: 子类必须实现此方法
        """
        pass

    def analyze_region(
        self,
        screen: np.ndarray,
        region_center: Tuple[int, int],
        region_size: Tuple[int, int] = (100, 100)
    ) -> np.ndarray:
        """分析指定区域

        Args:
            screen: 当前屏幕图像
            region_center: 区域中心坐标
            region_size: 区域大小

        Returns:
            np.ndarray: 区域图像
        """
        cx, cy = region_center
        w, h = region_size
        x1 = cx - w // 2
        y1 = cy - h // 2
        x2 = cx + w // 2
        y2 = cy + h // 2

        # 边界检查
        h, w = screen.shape[:2]
        x1 = max(0, x1)
        y1 = max(0, y1)
        x2 = min(w, x2)
        y2 = min(h, y2)

        return screen[y1:y2, x1:x2]

    def calculate_edge_density(self, image: np.ndarray) -> float:
        """计算图像边缘密度

        用于判断元素是否有明显的边框轮廓。

        Args:
            image: 图像区域

        Returns:
            float: 边缘密度 (0-1)
        """
        # 转为灰度
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # 边缘检测
        edges = cv2.Canny(gray, 50, 150)
        # 计算边缘像素比例
        return edges.sum() / (edges.size + 1e-6)

    def has_sharp_edges(self, image: np.ndarray, threshold: float = 0.1) -> bool:
        """判断是否有明显的锐利边缘

        Args:
            image: 图像区域
            threshold: 边缘密度阈值

        Returns:
            bool: 是否有锐利边缘
        """
        edge_density = self.calculate_edge_density(image)
        return edge_density > threshold

    def get_text_content(
        self,
        image: np.ndarray,
        ocr_enabled: bool = True
    ) -> Optional[str]:
        """提取图像中的文本内容

        Args:
            image: 图像区域
            ocr_enabled: 是否启用OCR

        Returns:
            Optional[str]: 提取的文本内容
        """
        if not ocr_enabled:
            return None

        try:
            import pytesseract
            # 转为灰度
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            # 二值化
            _, binary = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY)
            # 提取文本
            text = pytesseract.image_to_string(binary)
            return text.strip()
        except ImportError:
            print("pytesseract is not installed. Install with: pip install pytesseract and Tesseract-OCR")
            return None
        except Exception as e:
            print(f"OCR error: {e}")
            return None

    def detect_element_bounds(
        self,
        screen: np.ndarray,
        center_point: Tuple[int, int]
    ) -> Optional[Tuple[int, int, int, int]]:
        """检测元素边界框

        Args:
            screen: 原始屏幕图像
            center_point: 中心点坐标

        Returns:
            Optional[Tuple[int, int, int, int]]: (left, top, right, bottom) 边界框，或None
        """
        pixel_len = 5
        x, y = center_point
        h, w = screen.shape[:2]

        # 向四个方向扩展像素
        left = max(0, x - pixel_len)
        top = max(0, y - pixel_len)
        right = min(w - 1, x + pixel_len)
        bottom = min(h - 1, y + pixel_len)

        return (left, top, right, bottom)

    def get_elements_in_region(
        self,
        screen: np.ndarray,
        region_center: Tuple[int, int],
        region_size: Tuple[int, int] = (100, 100)
    ) -> list[UIElementInfo]:
        """检测区域内的所有元素

        Args:
            screen: 当前屏幕图像
            region_center: 区域中心坐标
            region_size: 区域大小

        Returns:
            list[UIElementInfo]: 元素信息列表
        """
        region = self.analyze_region(screen, region_center, region_size)

        # 默认检测点在中心
        element = self.detect(region, (region_size[0] // 2, region_size[1] // 2))

        if element and element.confidence >= self.confidence_threshold:
            # 还原到原始坐标
            cx, cy = region_center
            w, h = region_size
            x, y, rx, ry = element.bounding_box or (0, 0, 0, 0)
            left = cx - w // 2 + x
            right = left + rx
            top = cy - h // 2 + y
            bottom = top + ry

            element.bounding_box = (left, top, right, bottom)
            return [element]

        return []

    def clear_cache(self):
        """清空检测缓存"""
        self._element_cache.clear()
