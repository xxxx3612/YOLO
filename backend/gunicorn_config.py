"""
Gunicorn 配置文件
处理 worker 启动时的模型预加载
"""


def post_worker_init(worker):
    """Worker 进程启动后执行"""
    from app import get_yolo_model
    
    worker.log.info("Worker 启动，预加载 YOLO 模型...")
    try:
        get_yolo_model()
        worker.log.info("✅ 模型预加载完成")
    except Exception as e:
        worker.log.error(f"⚠️ 模型预加载失败: {e}")
