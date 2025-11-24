#!/usr/bin/env python3
"""
YOLO 姿态检测系统 - Flask 后端 API
开发环境配置
"""
import os
import base64
from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename
import cv2
import numpy as np
import torch
from ultralytics import YOLO
from datetime import datetime
from pathlib import Path
from head_pose_analyzer import analyze_head_pose

# GPU/CPU 设备检测
device = "cuda" if torch.cuda.is_available() else "cpu"
if torch.cuda.is_available():
    print(f"🚀 检测到GPU: {torch.cuda.get_device_name(0)}")
    print(
        f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB"
    )
else:
    print("💻 未检测到GPU，使用CPU模式")

# 性能优化设置（最大化速度，无内存限制）
torch.set_grad_enabled(False)  # 禁用梯度计算（仅推理）
# 环境变量不设置线程限制，让OpenMP/MKL自动优化

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

# COCO 骨架连接定义 (索引对)
SKELETON = [
    (0, 1),
    (0, 2),
    (1, 3),
    (2, 4),  # 头部
    (5, 6),
    (5, 7),
    (7, 9),
    (6, 8),
    (8, 10),  # 上肢
    (11, 12),
    (5, 11),
    (6, 12),  # 躯干
    (11, 13),
    (13, 15),
    (12, 14),
    (14, 16),  # 下肢
]


# 应用启动信息（Gunicorn 也会执行）
is_render = os.environ.get("RENDER") == "true"
if is_render:
    print("🎯 YOLO 姿态检测 API | Render 生产环境")
else:
    print("🎯 YOLO 姿态检测 API | 本地开发")


def get_yolo_model():
    """获取或加载 YOLO Pose 模型（线程安全，支持GPU/CPU）"""
    global yolo_model
    if yolo_model is None:
        try:
            model_path = MODEL_FOLDER / "yolo11n-pose.pt"
            if model_path.exists():
                print(f"正在加载本地姿态检测模型: {model_path}")
                yolo_model = YOLO(str(model_path))
            else:
                print("本地模型不存在，将下载 YOLO11n-pose...")
                yolo_model = YOLO("yolo11n-pose.pt")

            # 将模型移动到GPU或CPU
            yolo_model.to(device)

            print(f"✓ YOLO 姿态检测模型加载成功！")
            print(f"  运行设备: {device.upper()}")
            print(
                f"  关键点数量: {yolo_model.model.kpt_shape if hasattr(yolo_model.model, 'kpt_shape') else '17 (COCO format)'}"
            )
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


def perform_detection(
    image_path, confidence=0.25, iou=0.45, analyze_head_pose_enabled=False
):
    """执行 YOLO 姿态检测"""
    try:
        # 获取模型（延迟加载）
        model = get_yolo_model()

        # 读取图像
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError("无法读取图像")

        # 无尺寸限制，使用原始分辨率以获得最佳检测效果
        # YOLO 会自动处理图像尺寸优化

        # YOLO 姿态检测（使用GPU或CPU）
        results = model(image, conf=confidence, iou=iou, device=device)
        result = results[0]

        # 解析姿态检测结果
        detections = []
        if result.keypoints is not None and result.boxes is not None:
            keypoints_data = result.keypoints.cpu().numpy()
            boxes = result.boxes.cpu().numpy()

            for idx, (box, kpts) in enumerate(zip(boxes, keypoints_data.data)):
                # 提取关键点坐标和置信度
                keypoints_list = []
                for i in range(len(kpts)):
                    if len(kpts[i]) >= 2:  # 确保有 x, y 坐标
                        kp = {
                            "x": float(kpts[i][0]),
                            "y": float(kpts[i][1]),
                            "confidence": (
                                float(kpts[i][2]) if len(kpts[i]) > 2 else 0.0
                            ),
                        }
                        keypoints_list.append(kp)

                detection = {
                    "person_id": idx,
                    "bbox": {
                        "x1": float(box.xyxy[0][0]),
                        "y1": float(box.xyxy[0][1]),
                        "x2": float(box.xyxy[0][2]),
                        "y2": float(box.xyxy[0][3]),
                    },
                    "confidence": float(box.conf[0]),
                    "keypoints": keypoints_list,
                    "keypoint_count": len(keypoints_list),
                }
                detections.append(detection)

        # 头部姿态分析（可选）
        head_pose_stats = None
        if analyze_head_pose_enabled and detections:
            detections, head_pose_stats = analyze_head_pose(detections)

        # 绘制姿态检测结果
        if analyze_head_pose_enabled and detections:
            # 手动绘制，使用头部姿态对应的颜色
            annotated_image = image.copy()

            for detection in detections:
                head_pose = detection.get("head_pose", {})
                pose_type = head_pose.get("pose", "unknown")
                description = head_pose.get("description", "")
                angle = head_pose.get("head_angle")

                # 获取边界框
                bbox = detection["bbox"]
                x1, y1 = int(bbox["x1"]), int(bbox["y1"])
                x2, y2 = int(bbox["x2"]), int(bbox["y2"])

                # 根据姿态设置颜色 (BGR格式)
                if pose_type == "head_up":
                    color = (0, 165, 255)  # 橙色 - 抬头
                elif pose_type == "head_down":
                    color = (0, 0, 255)  # 红色 - 低头
                elif pose_type == "normal":
                    color = (0, 255, 0)  # 绿色 - 正常
                else:
                    color = (255, 0, 0)  # 蓝色 - 未知

                # 绘制检测框
                cv2.rectangle(annotated_image, (x1, y1), (x2, y2), color, 2)

                # 绘制关键点
                keypoints = detection["keypoints"]
                for kp in keypoints:
                    if kp["confidence"] > 0.5:
                        kp_x, kp_y = int(kp["x"]), int(kp["y"])
                        cv2.circle(annotated_image, (kp_x, kp_y), 3, color, -1)

                # 绘制姿态文本
                text = f"{description}"
                if angle is not None:
                    text += f" ({angle:.1f}deg)"

                # 添加置信度
                conf_text = f"{detection['confidence']*100:.1f}%"

                # 绘制文本背景
                (text_width, text_height), _ = cv2.getTextSize(
                    text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2
                )
                cv2.rectangle(
                    annotated_image,
                    (x1, y1 - text_height - 10),
                    (x1 + text_width + 10, y1),
                    color,
                    -1,
                )

                # 绘制文本
                cv2.putText(
                    annotated_image,
                    text,
                    (x1 + 5, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (255, 255, 255),
                    2,
                )

                # 绘制置信度（在框的右上角）
                cv2.putText(
                    annotated_image,
                    conf_text,
                    (x2 - 60, y1 + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    color,
                    2,
                )
        else:
            # 使用默认的YOLO绘制
            annotated_image = result.plot()

        # 将图像编码为 base64（高质量）
        encode_param = [cv2.IMWRITE_JPEG_QUALITY, 95]  # 95% 质量
        _, buffer = cv2.imencode(".jpg", annotated_image, encode_param)
        image_base64 = base64.b64encode(buffer).decode("utf-8")

        response_data = {
            "success": True,
            "detections": detections,
            "person_count": len(detections),
            "result_image": f"data:image/jpeg;base64,{image_base64}",
            "image_size": {"width": image.shape[1], "height": image.shape[0]},
        }

        # 添加头部姿态统计信息
        if head_pose_stats:
            response_data["head_pose_statistics"] = head_pose_stats

        return response_data

    except Exception as e:
        return {"success": False, "error": str(e)}


# ============ API 路由 ============


@app.route("/")
def index():
    """首页"""
    return jsonify(
        {
            "service": "YOLO 姿态检测 API",
            "version": "1.0.0",
            "status": "running",
            "model_loaded": yolo_model is not None,
            "model_type": "pose",
        }
    )


@app.route("/api/health", methods=["GET"])
def health_check():
    """健康检查"""
    model_loaded = yolo_model is not None
    return jsonify(
        {
            "status": "healthy",
            "service": "YOLO Pose Detection API",
            "model_loaded": model_loaded,
            "model_status": "loaded" if model_loaded else "will load on first request",
            "timestamp": datetime.now().isoformat(),
        }
    )


@app.route("/api/detect", methods=["POST", "OPTIONS"])
def detect():
    """图像姿态检测"""
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
        analyze_head_pose_enabled = (
            request.form.get("analyze_head_pose", "false").lower() == "true"
        )

        # 执行姿态检测
        result = perform_detection(filepath, confidence, iou, analyze_head_pose_enabled)

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
        return jsonify({"success": False, "error": f"姿态检测失败: {str(e)}"}), 500


@app.route("/api/keypoints", methods=["GET"])
def get_keypoints_info():
    """获取姿态关键点信息"""
    keypoints_coco = {
        "format": "COCO",
        "total": 17,
        "points": [
            {"id": 0, "name": "nose", "name_zh": "鼻子"},
            {"id": 1, "name": "left_eye", "name_zh": "左眼"},
            {"id": 2, "name": "right_eye", "name_zh": "右眼"},
            {"id": 3, "name": "left_ear", "name_zh": "左耳"},
            {"id": 4, "name": "right_ear", "name_zh": "右耳"},
            {"id": 5, "name": "left_shoulder", "name_zh": "左肩"},
            {"id": 6, "name": "right_shoulder", "name_zh": "右肩"},
            {"id": 7, "name": "left_elbow", "name_zh": "左肘"},
            {"id": 8, "name": "right_elbow", "name_zh": "右肘"},
            {"id": 9, "name": "left_wrist", "name_zh": "左腕"},
            {"id": 10, "name": "right_wrist", "name_zh": "右腕"},
            {"id": 11, "name": "left_hip", "name_zh": "左髋"},
            {"id": 12, "name": "right_hip", "name_zh": "右髋"},
            {"id": 13, "name": "left_knee", "name_zh": "左膝"},
            {"id": 14, "name": "right_knee", "name_zh": "右膝"},
            {"id": 15, "name": "left_ankle", "name_zh": "左踝"},
            {"id": 16, "name": "right_ankle", "name_zh": "右踝"},
        ],
    }
    return jsonify({"success": True, "keypoints": keypoints_coco})


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
    print("🎯 YOLO 姿态检测系统 - 开发服务器")
    print("=" * 60)
    print()
    print("✓ 系统就绪（姿态检测模型将在首次请求时加载）")
    print()

    # 从环境变量读取端口（Render 会设置 PORT）
    port = int(os.environ.get("PORT", 5000))
    host = "0.0.0.0"

    # 检测是否在 Render 环境（RENDER 变量由 Render 自动设置）
    is_render = os.environ.get("RENDER") == "true"
    render_service_name = os.environ.get("RENDER_SERVICE_NAME", "yolo-detection-api")
    render_external_url = os.environ.get(
        "RENDER_EXTERNAL_URL", "https://yolo-cp1y.onrender.com"
    )

    print("📍 服务地址:")
    if is_render and render_external_url:
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

    if is_render:
        print(f"☁️  Render 服务: {render_service_name}")
        print("🔧 生产模式: CPU-only PyTorch + Pose Detection")
    else:
        print("🔧 开发模式: 已启用代码热重载")

    print(f"💡 内存优化: 延迟加载模型")
    print(f"🤸 模型类型: YOLO11n-Pose（姿态检测）")
    print(f"⚙️  推理设备: {device.upper()}")
    if device == "cuda":
        print(f"   GPU加速已启用: {torch.cuda.get_device_name(0)}")
    print("按 Ctrl+C 停止服务器")
    print("=" * 60)
    print()

    # 启动 Flask 服务器
    # Render 环境禁用 debug 和 reloader 以避免重启问题
    app.run(
        host=host,
        port=port,
        debug=not is_render,  # Render 上禁用 debug
        use_reloader=not is_render,  # Render 上禁用 reloader
    )
