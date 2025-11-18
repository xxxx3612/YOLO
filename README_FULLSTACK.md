# 🎯 YOLO 目标检测系统 - 前后端协调指南

## 📋 项目概述

这是一个完整的 YOLO 目标检测系统，包含：
- **后端**: Flask API (Python)
- **前端**: Vue 3 + Vite
- **模型**: YOLOv8

---

## 🚀 快速启动

### 方式 1: 一键启动（推荐）

```bash
# Windows
start.bat
```

会自动：
1. 检查并安装依赖
2. 启动后端服务器（端口 5000）
3. 启动前端开发服务器（端口 5173）

### 方式 2: 分别启动

#### 启动后端

```bash
cd backend
python app.py
```

后端将在 `http://localhost:5000` 启动

#### 启动前端

```bash
cd frontend/vuefront
npm install  # 首次运行
npm run dev
```

前端将在 `http://localhost:5173` 启动

---

## 🔧 系统架构

### 后端 API (Flask)

**端口**: 5000  
**技术栈**: Flask + OpenCV + Ultralytics YOLO

**API 端点**:

| 端点 | 方法 | 说明 |
|------|------|------|
| `/` | GET | 服务信息 |
| `/api/health` | GET | 健康检查 |
| `/api/detect` | POST | 图像检测 |
| `/api/classes` | GET | 获取类别列表 |
| `/static/results/<filename>` | GET | 获取结果图片 |

**检测请求示例**:
```bash
curl -X POST http://localhost:5000/api/detect \
  -F "image=@test.jpg" \
  -F "confidence=0.25" \
  -F "iou=0.45"
```

**响应格式**:
```json
{
  "success": true,
  "detections": [
    {
      "class_id": 0,
      "class_name": "person",
      "confidence": 0.95,
      "bbox": {
        "x1": 100, "y1": 150,
        "x2": 200, "y2": 350
      }
    }
  ],
  "detection_count": 1,
  "result_image": "/static/results/result_20251118_123456.jpg",
  "image_size": {
    "width": 640,
    "height": 480
  }
}
```

### 前端 (Vue 3)

**端口**: 5173  
**技术栈**: Vue 3 + Vite

**环境配置**:
```bash
# frontend/vuefront/.env
VITE_API_URL=http://localhost:5000
```

**主要功能**:
- 图片上传
- 视频检测（开发中）
- 摄像头实时检测
- 结果可视化

---

## 📡 前后端通信

### CORS 配置

后端已配置 CORS，允许以下来源：
- `http://localhost:5173` (Vite 开发服务器)
- `http://localhost:3000` (备用端口)

### 数据流程

```
前端 (Vue)                    后端 (Flask)
    │                              │
    ├─ 上传图片 ──────────────────>│
    │   FormData                   │
    │   - image: File              │
    │   - confidence: 0.25         │
    │                              ├─ YOLO 检测
    │                              │
    │<─────────────── 返回结果 ────┤
    │   JSON                       │
    │   - detections               │
    │   - result_image             │
    │                              │
    ├─ 显示结果图 ────────────────>│
    │   GET /static/results/...    │
    │                              │
```

### 前端调用示例

```javascript
// App.vue
const handleDetect = async () => {
  const formData = new FormData()
  formData.append('image', selectedFile.value)
  formData.append('confidence', '0.25')
  
  const apiUrl = import.meta.env.VITE_API_URL
  const response = await fetch(`${apiUrl}/api/detect`, {
    method: 'POST',
    body: formData
  })
  
  const data = await response.json()
  if (data.success) {
    // 处理检测结果
    detectionResults.value = data.detections
    resultUrl.value = `${apiUrl}${data.result_image}`
  }
}
```

---

## 📁 目录结构

```
YOLO/
├── backend/                  # 后端代码
│   ├── app.py               # Flask 主应用（完整API）
│   ├── models/              # YOLO 模型文件
│   │   └── yolov8n.pt      # YOLOv8 nano 模型
│   ├── uploads/             # 临时上传目录
│   └── static/results/      # 检测结果图片
│
├── frontend/                 # 前端代码
│   └── vuefront/
│       ├── src/
│       │   └── App.vue      # 主组件（已更新API调用）
│       ├── .env             # 环境配置（API地址）
│       └── package.json
│
├── start.bat                # 一键启动脚本
└── README_FULLSTACK.md      # 本文档
```

---

## 🔍 测试流程

### 1. 测试后端

```bash
# 健康检查
curl http://localhost:5000/api/health

# 获取类别列表
curl http://localhost:5000/api/classes

# 测试检测（需要准备一张图片）
curl -X POST http://localhost:5000/api/detect \
  -F "image=@test.jpg"
```

### 2. 测试前端

1. 打开浏览器: `http://localhost:5173`
2. 上传一张图片
3. 点击"开始检测"
4. 查看检测结果

### 3. 端到端测试

1. 确保后端运行正常
2. 确保前端能访问
3. 在前端上传图片
4. 验证检测结果显示
5. 检查结果图片能否加载

---

## 🐛 常见问题

### Q1: CORS 错误

**症状**: 前端显示 CORS 错误  
**解决**: 
1. 确认后端已启动
2. 检查 `app.py` 中的 CORS 配置
3. 确认前端使用正确的 API 地址

### Q2: 模型下载失败

**症状**: 首次运行时模型下载失败  
**解决**:
1. 检查网络连接
2. 手动下载模型放到 `backend/models/yolov8n.pt`
3. 或使用国内镜像

### Q3: 端口被占用

**症状**: `Address already in use`  
**解决**:
```bash
# 修改后端端口（app.py 最后几行）
app.run(port=8000)  # 改为其他端口

# 修改前端配置（.env）
VITE_API_URL=http://localhost:8000
```

### Q4: 图片无法显示

**症状**: 检测结果返回但图片不显示  
**解决**:
1. 检查 `backend/static/results/` 目录权限
2. 确认图片 URL 正确
3. 查看浏览器控制台错误

---

## 🎨 自定义配置

### 修改检测参数

```javascript
// 前端 App.vue
formData.append('confidence', '0.3')  // 置信度阈值
formData.append('iou', '0.5')         // IoU 阈值
```

### 修改模型

```python
# 后端 app.py
# 使用更大的模型（更准确但更慢）
yolo_model = YOLO('yolov8m.pt')  # medium
yolo_model = YOLO('yolov8l.pt')  # large
yolo_model = YOLO('yolov8x.pt')  # extra large
```

### 添加新功能

1. **后端添加端点**:
```python
@app.route('/api/new-feature', methods=['POST'])
def new_feature():
    # 你的代码
    return jsonify({...})
```

2. **前端调用**:
```javascript
const response = await fetch(`${apiUrl}/api/new-feature`, {
  method: 'POST',
  body: data
})
```

---

## 📊 性能优化

### 后端优化

1. **使用更小的模型**: `yolov8n.pt` (最快)
2. **降低图片分辨率**: 在检测前缩放图片
3. **批量处理**: 一次处理多张图片

### 前端优化

1. **图片压缩**: 上传前压缩图片
2. **懒加载**: 结果图片使用懒加载
3. **缓存**: 缓存检测结果

---

## 📄 依赖清单

### 后端依赖

```txt
flask>=3.0.0
flask-cors>=4.0.0
opencv-python>=4.8.0
ultralytics>=8.0.0
torch>=2.0.0
torchvision>=0.15.0
```

安装:
```bash
pip install flask flask-cors opencv-python ultralytics torch torchvision
```

### 前端依赖

```json
{
  "dependencies": {
    "vue": "^3.3.0"
  },
  "devDependencies": {
    "vite": "^5.0.0"
  }
}
```

安装:
```bash
cd frontend/vuefront
npm install
```

---

## 🚀 部署到生产

### 后端部署

1. 使用 Gunicorn:
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. 使用 Docker:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "app.py"]
```

### 前端部署

```bash
cd frontend/vuefront
npm run build
# dist/ 目录可以部署到静态服务器
```

---

## 📞 支持

- **问题反馈**: GitHub Issues
- **文档**: 查看各目录下的 README
- **示例**: 查看 `examples/` 目录

---

**最后更新**: 2025年11月18日  
**版本**: 1.0.0  
**维护者**: xxxx3612
