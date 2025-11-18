# YOLO Object Detection System

基于 YOLOv8 的目标检测系统，支持图片、视频和摄像头实时检测。

## 环境要求
- Python 3.11+
- Node.js 18+
- Git 2.51.0+

## 技术栈

### 后端
- Flask 3.1.0
- Flask-CORS
- OpenCV (cv2)
- Ultralytics YOLOv8
- PyTorch

### 前端
- Vue 3
- Vite

## 快速启动

### 方式一：一键启动（推荐）
```bash
start.bat
```

### 方式二：手动启动

#### 启动后端
```bash
cd backend
pip install flask flask-cors opencv-python ultralytics torch torchvision
python app.py
```
后端运行在 http://localhost:5000

#### 启动前端
```bash
cd frontend/vuefront
npm install
npm run dev
```
前端运行在 http://localhost:5173

## 使用说明

1. 在浏览器访问 http://localhost:5173
2. 选择检测模式（图片/视频/摄像头）
3. 上传文件或打开摄像头
4. 点击"开始检测"查看结果

## 项目结构
```
YOLO/
├── backend/          # Flask 后端
│   ├── app.py       # 主应用
│   ├── models/      # YOLO 模型文件
│   ├── uploads/     # 临时上传目录
│   └── static/results/  # 检测结果图片
├── frontend/vuefront/   # Vue 前端
│   └── src/App.vue
└── start.bat        # 一键启动脚本
```

## API 文档

详见 [README_FULLSTACK.md](README_FULLSTACK.md)