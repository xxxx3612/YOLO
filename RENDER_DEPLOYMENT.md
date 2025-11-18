# YOLO Detection System - Render Deployment Guide

## 部署到 Render

### 前提条件
- GitHub 账号
- Render 账号（免费版即可）
- 代码已推送到 GitHub 仓库

### 部署步骤

#### 1. 准备代码
确保以下文件已正确配置：
- ✅ `render.yaml` - Render 配置文件
- ✅ `requirements.txt` - Python 依赖（包含 YOLO 相关库）
- ✅ `backend/app.py` - 使用 `PORT` 环境变量
- ✅ `.gitignore` - 忽略 `start.bat` 等本地文件

#### 2. 推送到 GitHub
```bash
git add .
git commit -m "Deploy to Render"
git push origin main
```

#### 3. 在 Render 创建服务

##### 方式一：使用 Blueprint（推荐）
1. 登录 [Render Dashboard](https://dashboard.render.com/)
2. 点击 "New" → "Blueprint"
3. 连接你的 GitHub 仓库
4. Render 会自动读取 `render.yaml` 并创建两个服务：
   - `yolo-detection-api` - 后端 API
   - `yolo-detection-frontend` - Vue 前端

##### 方式二：手动创建
如果 Blueprint 方式失败，手动创建：

**后端服务：**
1. New → Web Service
2. 连接 GitHub 仓库
3. 配置：
   - Name: `yolo-detection-api`
   - Environment: `Python 3`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `cd backend && python app.py`
   - Instance Type: Free

**前端服务：**
1. New → Web Service
2. 连接同一个仓库
3. 配置：
   - Name: `yolo-detection-frontend`
   - Environment: `Node`
   - Build Command: `cd frontend/vuefront && npm install && npm run build`
   - Start Command: `cd frontend/vuefront && npm run preview -- --host 0.0.0.0 --port $PORT`
   - Environment Variable:
     - `VITE_API_URL` = `https://yolo-detection-api.onrender.com`（替换为你的后端 URL）

#### 4. 等待部署完成
- 初次部署可能需要 10-15 分钟（下载 YOLO 模型）
- 查看日志确认是否成功

#### 5. 获取服务 URL
部署成功后，Render 会提供两个 URL：
- 后端: `https://yolo-detection-api.onrender.com`
- 前端: `https://yolo-detection-frontend.onrender.com`

### 重要配置说明

#### 端口配置
后端会自动使用 Render 提供的 `PORT` 环境变量：
```python
port = int(os.environ.get('PORT', 5000))
app.run(host='0.0.0.0', port=port)
```

#### CORS 配置
需要在后端允许前端域名访问。如果前端 URL 是 `https://yolo-detection-frontend.onrender.com`，需要更新 `backend/app.py` 的 CORS 配置：

```python
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:5173",
            "http://localhost:3000",
            "https://yolo-detection-frontend.onrender.com"  # 添加生产环境 URL
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
```

#### 前端 API 配置
更新 `frontend/vuefront/.env`：
```bash
VITE_API_URL=https://yolo-detection-api.onrender.com
```

然后重新构建前端。

### 常见问题

#### Q1: 服务启动失败
**检查：**
1. 查看 Render 日志
2. 确认 `requirements.txt` 包含所有依赖
3. 确认 `python app.py` 能正常启动

#### Q2: YOLO 模型下载失败
**解决：**
1. Render 免费版磁盘空间有限
2. 考虑使用更小的模型（`yolov8n.pt`）
3. 或手动上传模型文件到 `backend/models/`

#### Q3: CORS 错误
**解决：**
1. 确认后端 CORS 配置包含前端域名
2. 检查前端 `.env` 中的 `VITE_API_URL` 是否正确
3. 重新部署后端和前端

#### Q4: 免费版服务休眠
Render 免费版服务 15 分钟无请求后会休眠，下次访问需要重新启动（约 30 秒）。

**解决方案：**
- 升级到付费版
- 使用定时 ping 服务（如 UptimeRobot）

### 性能优化

#### 减少冷启动时间
1. 使用较小的 YOLO 模型（`yolov8n.pt`）
2. 优化依赖（只安装必要的包）

#### 降低内存使用
```python
# 在 app.py 中限制 YOLO 模型占用
yolo_model = YOLO('yolov8n.pt')  # 使用 nano 版本
```

### 本地测试 Render 配置

在推送前，本地测试 Render 配置：

```bash
# 设置 PORT 环境变量
set PORT=8000  # Windows
export PORT=8000  # Linux/Mac

# 启动后端
cd backend
python app.py

# 启动前端（新终端）
cd frontend/vuefront
npm run build
npm run preview -- --port 3000
```

### 监控和日志

- **查看实时日志**: Render Dashboard → 选择服务 → Logs
- **检查健康状态**: 访问 `https://your-api.onrender.com/api/health`

---

## 部署清单

部署前确认：
- [ ] 代码已推送到 GitHub
- [ ] `render.yaml` 配置正确
- [ ] `requirements.txt` 包含所有依赖
- [ ] `.gitignore` 忽略本地文件（`start.bat`）
- [ ] 后端使用 `PORT` 环境变量
- [ ] CORS 配置包含生产域名
- [ ] 前端 `.env` 配置正确

---

**祝部署顺利！** 🚀
