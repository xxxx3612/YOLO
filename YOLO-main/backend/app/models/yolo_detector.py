import cv2
import numpy as np
from ultralytics import YOLO
import os
from datetime import datetime
from ..config import config


class YOLODetector:
    def __init__(self):
        self.model = None
        self.load_model()

    def load_model(self):
        """加载YOLO模型"""
        try:
            print("正在加载YOLO模型...")
            # 使用预训练的YOLOv8模型
            self.model = YOLO(config.MODEL_NAME)
            print(f"模型 {config.MODEL_NAME} 加载成功!")

            # 打印模型信息
            print(f"模型类别数: {len(self.model.names)}")
            print("支持的类别:", list(self.model.names.values())[:10])  # 只显示前10个

        except Exception as e:
            print(f"模型加载失败: {e}")
            raise

    def detect_image(self, image_path, save_result=True):
        """检测单张图像"""
        try:
            # 读取图像
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError("无法读取图像文件")

            print(f"检测图像: {os.path.basename(image_path)}, 尺寸: {image.shape}")

            # 使用YOLO进行检测
            results = self.model(
                image,
                conf=config.CONFIDENCE_THRESHOLD,
                iou=config.IOU_THRESHOLD,
                imgsz=config.IMAGE_SIZE
            )

            # 解析检测结果
            detections = self._parse_detections(results[0])

            # 保存结果图像
            result_image_path = None
            if save_result and len(detections) > 0:
                result_image_path = self._save_result_image(results[0], image_path)

            print(f"检测完成，发现 {len(detections)} 个目标")

            return {
                'success': True,
                'detections': detections,
                'result_image': result_image_path,
                'image_size': {
                    'width': image.shape[1],
                    'height': image.shape[0]
                }
            }

        except Exception as e:
            print(f"检测失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def detect_batch(self, image_paths):
        """批量检测图像（简化版）"""
        batch_results = []

        for image_path in image_paths:
            result = self.detect_image(image_path)
            batch_results.append(result)

        return batch_results

    def _parse_detections(self, result):
        """解析YOLO检测结果"""
        detections = []

        if result.boxes is not None:
            boxes = result.boxes.cpu().numpy()

            for i in range(len(boxes)):
                box = boxes[i]
                detection = {
                    'class_id': int(box.cls[0]),
                    'class_name': result.names[int(box.cls[0])],
                    'confidence': float(box.conf[0]),
                    'bbox': {
                        'x1': float(box.xyxy[0][0]),
                        'y1': float(box.xyxy[0][1]),
                        'x2': float(box.xyxy[0][2]),
                        'y2': float(box.xyxy[0][3]),
                        'width': float(box.xyxy[0][2] - box.xyxy[0][0]),
                        'height': float(box.xyxy[0][3] - box.xyxy[0][1])
                    }
                }
                detections.append(detection)

        return detections

    def _save_result_image(self, result, original_path):
        """保存带检测结果的图像"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            original_name = os.path.splitext(os.path.basename(original_path))[0]
            result_filename = f"{original_name}_{timestamp}.jpg"
            result_path = os.path.join(config.RESULT_FOLDER, result_filename)

            # 保存结果图像
            result.save(filename=result_path)

            return f"/static/results/{result_filename}"

        except Exception as e:
            print(f"保存结果图像失败: {e}")
            return None

    def get_class_names(self):
        """获取类别名称列表"""
        return self.model.names if self.model else {}


# 创建全局检测器实例
detector = YOLODetector()