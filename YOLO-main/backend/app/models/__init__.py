# 使models目录成为Python包
from .yolo_detector import YOLODetector, detector

__all__ = ['YOLODetector', 'detector']