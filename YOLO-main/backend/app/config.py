import os
import yaml
from pathlib import Path


class Config:
    """
    应用配置类
    从YAML文件加载配置信息
    """

    def __init__(self, config_path='config.yaml'):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.load_config()

    def load_config(self):
        """加载配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config_data = yaml.safe_load(file)
        except FileNotFoundError:
            # 如果配置文件不存在，使用默认配置
            print(f"配置文件 {self.config_path} 未找到，使用默认配置")
            config_data = self.get_default_config()

        # 应用配置
        self.APP_NAME = config_data.get('app', {}).get('name', 'YOLO Vision System')
        self.APP_VERSION = config_data.get('app', {}).get('version', '1.0.0')
        self.DEBUG = config_data.get('app', {}).get('debug', False)

        # 服务器配置
        self.HOST = config_data.get('server', {}).get('host', '0.0.0.0')
        self.PORT = config_data.get('server', {}).get('port', 5000)

        # 模型配置
        self.MODEL_NAME = config_data.get('model', {}).get('name', 'yolov8n.pt')
        self.CONFIDENCE_THRESHOLD = config_data.get('model', {}).get('confidence_threshold', 0.25)
        self.IOU_THRESHOLD = config_data.get('model', {}).get('iou_threshold', 0.45)
        self.IMAGE_SIZE = config_data.get('model', {}).get('image_size', 640)

        # 上传配置
        self.ALLOWED_EXTENSIONS = set(config_data.get('upload', {}).get('allowed_extensions', ['jpg', 'jpeg', 'png']))
        self.MAX_FILE_SIZE = config_data.get('upload', {}).get('max_file_size', 16 * 1024 * 1024)
        self.UPLOAD_FOLDER = config_data.get('upload', {}).get('upload_folder', 'uploads')
        self.RESULT_FOLDER = config_data.get('upload', {}).get('result_folder', 'static/results')

        # 创建必要的目录
        Path(self.UPLOAD_FOLDER).mkdir(exist_ok=True)
        Path(self.RESULT_FOLDER).mkdir(exist_ok=True, parents=True)

        print(f"配置加载完成: {self.APP_NAME} v{self.APP_VERSION}")

    def get_default_config(self):
        """获取默认配置"""
        return {
            'app': {
                'name': 'YOLO Vision System',
                'version': '1.0.0',
                'debug': False
            },
            'server': {
                'host': '0.0.0.0',
                'port': 5000
            },
            'model': {
                'name': 'yolov8n.pt',
                'confidence_threshold': 0.25,
                'iou_threshold': 0.45,
                'image_size': 640
            },
            'upload': {
                'allowed_extensions': ['jpg', 'jpeg', 'png', 'bmp', 'tiff', 'webp'],
                'max_file_size': 16777216,
                'upload_folder': 'uploads',
                'result_folder': 'static/results'
            }
        }


# 创建全局配置实例
config = Config()