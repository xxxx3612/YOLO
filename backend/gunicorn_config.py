"""
Gunicorn 配置文件
处理 worker 启动时的姿态检测模型预加载
"""


def post_worker_init(worker):
    """Worker 进程启动后执行 - 预加载 YOLO Pose 模型"""
    from app import get_yolo_model
    
    worker.log.info("Worker 启动，预加载 YOLO 模型...")
    try:
        get_yolo_model()
        worker.log.info("✅ 姿态检测模型预加载完成，系统就绪")
    except Exception as e:
        worker.log.error(f"❌ 模型预加载失败: {e}")
