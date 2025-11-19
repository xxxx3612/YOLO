#!/usr/bin/env python3
"""
YOLO 目标检测系统 - Flask 后端 API
开发环境配置
"""
import os
import base64
import gc
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from datetime import datetime
from pathlib import Path

# 内存优化设置
torch.set_num_threads(1)  # 限制 PyTorch CPU 线程数
torch.set_grad_enabled(False)  # 禁用梯度计算（仅推理）
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# 配置
BASE_DIR = Path(__file__).parent
UPLOAD_FOLDER = BASE_DIR / "uploads"
MODEL_FOLDER = BASE_DIR / "models"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "bmp", "webp"}
MAX_FILE_SIZE = 16 * 1024 * 1024  # 16MB

# 创建必要目录
UPLOAD_FOLDER.mkdir(exist_ok=True)
MODEL_FOLDER.mkdir(exist_ok=True)

# 创建 Flask 应用
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = MAX_FILE_SIZE
app.config["UPLOAD_FOLDER"] = str(UPLOAD_FOLDER)

# 启用 CORS，允许前端跨域访问
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": [
                "http://localhost:5173",
                "http://localhost:3000",
                "https://yolofrontend.onrender.com",  # Render前端
            ],
            "methods": ["GET", "POST", "OPTIONS"],
            "allow_headers": ["Content-Type"],
        }
    },
)

# 全局 YOLO 模型
yolo_model = None


def get_yolo_model():
    """延迟加载 YOLO 模型（首次请求时加载）"""
    global yolo_model
    if yolo_model is None:
        try:
            model_path = MODEL_FOLDER / "yolov8n.pt"
            if model_path.exists():
                print(f"正在加载本地模型: {model_path}")
                yolo_model = YOLO(str(model_path))
            else:
                print("本地模型不存在，将下载 YOLOv8n...")
                yolo_model = YOLO("yolov8n.pt")

            print(f"✓ YOLO 模型加载成功！")
            print(f"  支持的类别数: {len(yolo_model.names)}")
        except Exception as e:
            print(f"✗ 模型加载失败: {e}")
            raise
    return yolo_model


def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def save_uploaded_file(file):
    """保存上传的文件"""
    if file and allowed_file(file.filename):
        # 生成安全文件名
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{original_filename}"
        filepath = UPLOAD_FOLDER / filename

        file.save(str(filepath))
        return str(filepath), filename
    return None, None


def perform_detection(image_path, confidence=0.25, iou=0.45):
    """执行 YOLO 目标检测"""
    try:
        # 获取模型（延迟加载）
        model = get_yolo_model()

        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("无法读取图像")

        # 限制图像尺寸以减少内存占用
        max_dimension = 640
        height, width = image.shape[:2]
        if max(height, width) > max_dimension:
            scale = max_dimension / max(height, width)
            new_width = int(width * scale)
            new_height = int(height * scale)
            image = cv2.resize(
                image, (new_width, new_height), interpolation=cv2.INTER_AREA
            )

        # YOLO 检测
        results = model(image, conf=confidence, iou=iou)
        result = results[0]

        # 解析检测结果
        detections = []
        if result.boxes is not None:
            boxes = result.boxes.cpu().numpy()
            for box in boxes:
                detection = {
                    "class_id": int(box.cls[0]),
                    "class_name": model.names[int(box.cls[0])],
                    "confidence": float(box.conf[0]),
                    "bbox": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3]),
                    },
                }
                detections.append(detection)

        # 绘制检测结果
        annotated_image = result.plot()

        # 将图像编码为 base64，降低质量以节省内存
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 85]  # 85% 质量（默认 95）
        _, buffer = cv2.imencode(".jpg", annotated_image, encode_param)
        image_base64 = base64.b64encode(buffer).decode("utf-8")

        return {
            "success": True,
            "detections": detections,
            "detection_count": len(detections),
            "result_image": f"data:image/jpeg;base64,{image_base64}",
            "image_size": {"width": image.shape[1], "height": image.shape[0]},
        }

    except Exception as e:
        return {"success": False, "error": str(e)}
    finally:
        # 清理内存
        gc.collect()


# ============ API 路由 ============


@app.route("/")
def index():
    """首页"""
    return jsonify(
        {
            "service": "YOLO 目标检测 API",
            "version": "1.0.0",
            "status": "running",
            "model_loaded": yolo_model is not None,
        }
    )


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查"""
    model_loaded = yolo_model is not None
    return jsonify(
        {
            "status": "healthy",
            "service": "YOLO Detection API",
            "model_loaded": model_loaded,
            "model_status": "loaded" if model_loaded else "will load on first request",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/detect", methods=["POST", "OPTIONS"])
def detect():
    """图像目标检测"""
    if request.method == "OPTIONS":
        return "", 204

    try:
        # 检查模型是否可用（延迟加载会在这里触发）
        try:
            get_yolo_model()
        except Exception as e:
            return jsonify({"success": False, "error": f"模型加载失败: {str(e)}"}), 500

        # 检查文件
        if "image" not in request.files:
            return jsonify({"success": False, "error": "未提供图像文件"}), 400

        file = request.files["image"]

        if file.filename == "":
            return jsonify({"success": False, "error": "未选择文件"}), 400

        if not allowed_file(file.filename):
            return (
                jsonify(
                    {
                        "success": False,
                        "error": f'不支持的文件类型，允许的类型: {", ".join(ALLOWED_EXTENSIONS)}',
                    }
                ),
                400,
            )

        # 保存上传文件
        filepath, filename = save_uploaded_file(file)
        if not filepath:
            return jsonify({"success": False, "error": "文件保存失败"}), 500

        # 获取检测参数
        confidence = float(request.form.get("confidence", 0.25))
        iou = float(request.form.get("iou", 0.45))

        # 执行检测
        result = perform_detection(filepath, confidence, iou)

        # 清理上传的临时文件
        try:
            os.remove(filepath)
        except:
            pass

        if result["success"]:
            return jsonify(result)
        else:
            return jsonify(result), 500

    except Exception as e:
        return jsonify({"success": False, "error": f"检测失败: {str(e)}"}), 500


@app.route("/api/classes", methods=["GET"])
def get_classes():
    """获取支持的类别列表"""
    try:
        model = get_yolo_model()
        return jsonify(
            {
                "success": True,
                "classes": model.names,
                "total_classes": len(model.names),
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": f"模型未加载: {str(e)}"}), 500


@app.errorhandler(413)
def request_entity_too_large(error):
    """文件过大错误处理"""
    return (
        jsonify(
            {
                "success": False,
                "error": f"文件过大，最大允许 {MAX_FILE_SIZE // (1024 * 1024)}MB",
            }
        ),
        413,
    )


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({"success": False, "error": "请求的资源不存在"}), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    return jsonify({"success": False, "error": "服务器内部错误"}), 500


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 YOLO 目标检测系统 - 开发服务器")
    print("=" * 60)
    print()
    print("✓ 系统就绪（模型将在首次请求时加载）")
    print()

    # 从环境变量读取端口（Render 会设置 PORT）
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"

    # 检测是否在 Render 环境
    render_service_name = os.environ.get("RENDER_SERVICE_NAME")
    render_external_url = os.environ.get("RENDER_EXTERNAL_URL")

    print("📍 服务地址:")
    if render_external_url:
        # Render 生产环境
        print(f"   - 外部访问: {render_external_url}")
        print(f"   - API:     {render_external_url}/api/detect")
        print(f"   - 健康检查: {render_external_url}/api/health")
    else:
        # 本地开发环境
        print(f"   - 本地:    http://localhost:{port}")
        print(f"   - API:     http://localhost:{port}/api/detect")
        print(f"   - 健康检查: http://localhost:{port}/api/health")

    print()
    print("📁 文件存储:")
    print(f"   - 上传目录: {UPLOAD_FOLDER}")
    print(f"   - 模型目录: {MODEL_FOLDER}")
    print()

    if render_service_name:
        print(f"☁️  Render 服务: {render_service_name}")
        print("🔧 生产模式: CPU-only PyTorch")
    else:
        print("🔧 开发模式: 已启用代码热重载")

    print("💡 内存优化: 延迟加载模型 + CPU-only PyTorch")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    # 启动 Flask 服务器
    # Render 环境禁用 debug 和 reloader 以避免重启问题
    is_render = bool(render_service_name)
    app.run(
        host=host,
        port=port,
        debug=not is_render,  # Render 上禁用 debug
        use_reloader=not is_render,  # Render 上禁用 reloader
    )
