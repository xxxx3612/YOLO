# 内存优化指南 - Render 512MB 限制

## 问题
Render 免费版限制为 512MB 内存，YOLO 模型和依赖可能超出此限制。

## 优化方案

### 1. 使用最小模型（推荐）
YOLOv8 Nano 是最小版本，但仍可能占用较多内存。

**替代方案**：
```python
# backend/app.py 中修改
yolo_model = YOLO("yolov8n.pt")  # 当前：约 6MB 模型，运行时 200-300MB
```

### 2. 延迟加载模型
不在启动时加载模型，首次请求时再加载：

```python
# 修改 load_yolo_model() 为按需加载
def get_yolo_model():
    global yolo_model
    if yolo_model is None:
        yolo_model = YOLO("yolov8n.pt")
    return yolo_model
```

### 3. 减少依赖体积

#### 方案 A: 使用 CPU-only PyTorch（推荐）
```txt
# requirements.txt
torch==2.5.1+cpu
torchvision==0.20.1+cpu
--find-links https://download.pytorch.org/whl/torch_stable.html
```

#### 方案 B: 移除测试依赖
```txt
# 删除不必要的包
# pytest>=7.4.3  # 生产环境不需要
# black>=23.11.0
# flake8>=6.1.0
```

### 4. 优化图像处理

**限制输入图像大小**：
```python
# backend/app.py
def perform_detection(image_path, confidence=0.25, iou=0.45):
    image = cv2.imread(image_path)
    
    # 限制图像尺寸，减少内存占用
    max_dimension = 640
    height, width = image.shape[:2]
    if max(height, width) > max_dimension:
        scale = max_dimension / max(height, width)
        new_width = int(width * scale)
        new_height = int(height * scale)
        image = cv2.resize(image, (new_width, new_height))
    
    # 继续检测...
```

### 5. 使用轻量级 Web 服务器

**当前问题**：Flask 开发服务器 + YOLO 模型占用较多内存

**解决方案**：使用 Gunicorn 单进程模式
```yaml
# render.yaml
startCommand: cd backend && gunicorn --workers 1 --threads 2 --timeout 120 app:app
```

添加到 requirements.txt：
```txt
gunicorn==21.2.0
```

### 6. 清理临时文件
```python
# 在检测后立即删除上传的文件
def perform_detection(image_path, confidence=0.25, iou=0.45):
    try:
        # ... 检测代码 ...
        return result
    finally:
        # 确保删除临时文件
        if os.path.exists(image_path):
            os.remove(image_path)
```

### 7. 使用环境变量控制内存

**设置 PyTorch 内存限制**：
```python
# backend/app.py 顶部添加
import torch
torch.set_num_threads(1)  # 限制 CPU 线程数
```

```yaml
# render.yaml 添加环境变量
envVars:
  - key: OMP_NUM_THREADS
    value: "1"
  - key: MKL_NUM_THREADS
    value: "1"
```

### 8. 监控内存使用

添加内存监控端点：
```python
import psutil

@app.route('/api/memory', methods=['GET'])
def get_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    return jsonify({
        'rss_mb': memory_info.rss / 1024 / 1024,
        'vms_mb': memory_info.vms / 1024 / 1024
    })
```

## 推荐组合方案

### 方案 A: 最小化配置（最推荐）
1. 使用 CPU-only PyTorch
2. 移除测试依赖
3. 限制图像尺寸为 640px
4. 使用 Gunicorn 单进程
5. 立即清理临时文件

### 方案 B: 如果方案 A 仍超内存
考虑升级到 Render 付费版（$7/月，512MB → 2GB）或使用其他平台：
- Railway (512MB 免费，$5/月 8GB)
- Fly.io (256MB 免费，可扩展)
- Hugging Face Spaces (免费 16GB，专为 ML 模型优化)

## 实施步骤

1. **立即优化**：
```bash
# 修改 requirements.txt 移除测试依赖
# 添加图像尺寸限制到 app.py
git commit -m "Optimize memory usage for Render"
git push
```

2. **监控部署**：
- 查看 Render 日志中的内存使用
- 访问 `/api/memory` 查看实时内存

3. **如果仍超限**：
- 切换到 CPU-only PyTorch
- 或考虑付费方案

## 预期效果

| 优化项 | 内存节省 |
|--------|---------|
| 移除测试依赖 | ~50MB |
| CPU-only PyTorch | ~200MB |
| 图像尺寸限制 | ~100MB |
| Gunicorn 单进程 | ~50MB |
| **总计** | **~400MB** |

优化后内存使用应在 **300-400MB** 范围内，可在 512MB 限制内运行。
