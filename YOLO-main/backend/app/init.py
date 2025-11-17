from flask import Flask
from flask_cors import CORS  # 处理跨域请求
from flask_restx import Api
from .config import config
from .routes.api import api


def create_app():
    # 创建Flask应用实例
    app = Flask(__name__)
    app.config.from_object(config)  # 加载配置

    # 启用CORS，允许跨域请求
    CORS(app)

    # 配置Flask-RESTx API文档
    restx_api = Api(
        app,
        version=config.APP_VERSION,
        title=config.APP_NAME,
        description='基于YOLO的视觉识别系统API',
        doc='/docs/'  # API文档访问路径
    )

    # 注册API命名空间
    restx_api.add_namespace(api, path='/api')

    return app