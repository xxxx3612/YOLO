# YOLO 姿态检测与行为分析系统

基于 YOLO11-Pose 的智能姿态检测系统，支持关键点识别与头部姿态（抬头/低头）分析。

## ✨ 功能特性

- **多模式检测**：支持图片上传、视频文件分析及摄像头实时检测。
- **姿态关键点**：基于 YOLO11n-pose 模型，精准识别 17 个主要人体关键点。
- **头部姿态分析**：
  - 智能识别抬头、低头及正常视线状态。
  - 动态颜色标注：🟧 抬头 | 🟥 低头 | 🟩 正常 | 🟦 未知。
- **实时性能**：针对 GPU 优化，支持流畅的实时视频流分析。
- **现代化 UI**：基于 Vue 3 的响应式界面，提供直观的可视化结果与统计数据。

## 🛠️ 技术栈

### 后端 (Backend)
- **框架**: Flask
- **AI 模型**: Ultralytics YOLO11n-pose
- **图像处理**: OpenCV
- **核心逻辑**: `head_pose_analyzer.py` (自定义头部角度算法)

### 前端 (Frontend)
- **框架**: Vue 3 + Vite
- **样式**: CSS3 (Flexbox/Grid)

## 🚀 快速启动

### 方式一：一键启动（Windows）
双击运行根目录下的 `start.bat` 脚本。

### 方式二：手动启动

#### 1. 启动后端
```bash
cd backend
# 安装依赖
pip install -r requirements.txt
# 启动服务
python app.py
```
后端服务将运行在: `http://localhost:5000`

#### 2. 启动前端
```bash
cd frontend/vuefront
# 安装依赖
npm install
# 启动开发服务器
npm run dev
```
前端页面将运行在: `http://localhost:5173`

## 📂 项目结构

```
YOLO/
├── backend/
│   ├── app.py                 # Flask 主应用入口
│   ├── head_pose_analyzer.py  # 头部姿态分析核心算法
│   ├── yolo11n-pose.pt        # YOLO 姿态检测模型
│   ├── models/                # 模型存放目录
│   └── uploads/               # 临时文件存储
├── frontend/vuefront/
│   ├── src/
│   │   ├── App.vue            # 主组件逻辑
│   │   ├── AppStyles.css      # 组件样式
│   │   ├── theme-override.css # 主题样式覆盖
│   │   └── main.js            # 入口文件
│   └── ...
├── start.bat                  # 一键启动脚本
└── README.md                  # 项目文档
```

## 📝 使用说明

1. **选择模式**：在左侧侧边栏选择「图片」、「视频」或「实时」模式。
2. **上传/启动**：上传本地文件或点击打开摄像头。
3. **功能开关**：勾选「启用头部姿态分析」以开启抬头/低头识别功能。
4. **查看结果**：
   - 右侧面板显示检测统计数据（人数、姿态分布）。
   - 画面中实时绘制彩色检测框与关键点。
   - 支持下载检测后的结果图片。

## 🔧 环境要求
- Python 3.8+
- Node.js 16+
- CUDA (可选，推荐用于 GPU 加速)