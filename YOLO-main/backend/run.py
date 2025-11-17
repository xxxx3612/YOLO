#!/usr/bin/env python3
"""
YOLO视觉识别系统启动脚本
"""
import os
import sys

# 添加当前目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    """主函数"""
    # 创建Flask应用
    app = create_app()

    # 启动开发服务器
    print(f"启动 YOLO视觉识别系统...")
    print(f"访问地址: http://localhost:5000")
    print(f"API文档: http://localhost:5000/docs/")

    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )


if __name__ == '__main__':
    main()