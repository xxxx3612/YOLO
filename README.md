# INT617group assessment
使用YOLO模型创建一个视觉识别系统   
使用github action完成CI/CD流程   

使用flask打包后端，API
使用VUE进行前端页面的编写
使用render

## 环境
- git version 2.51.0.windows.1   
- conda 25.5.1   
- python 3.11

## 主要依赖
### 后端
- Flask (v3.0.0)

### 前端
- Vue.js (v3.3.8)

### 测试
- Black (v23.11.0)
- Flake8 (v6.1.0)
- pytest (v7.4.3)

## 启动方式

### 启动后端（Flask）
1. 打开终端，进入 backend 目录：
   ```bash
   cd backend
   ```
2. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```
3. 启动后端服务：
   ```bash
   python app.py
   ```
   后端服务默认运行在 http://localhost:5000

### 启动前端（Vue）
1. 打开新终端，进入 frontend 目录：
   ```bash
   cd frontend
   ```
2. 安装依赖：
   ```bash
   npm install
   ```
3. 启动前端开发服务器：
   ```bash
   npm run dev
   ```
   前端页面默认运行在 http://localhost:5173

### 访问项目
- 在浏览器中访问 http://localhost:5173
- 输入表达式，点击按钮即可体验前后端联动的计算器

如遇到依赖安装或端口占用等问题，请将报错信息反馈，我会协助排查。