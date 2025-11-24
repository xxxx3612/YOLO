<script setup>
import { ref, onUnmounted } from 'vue'

// 状态管理
const mode = ref('image')
const selectedFile = ref(null)
const previewUrl = ref(null)
const resultUrl = ref(null)
const isDetecting = ref(false)
const detectionResults = ref(null)
const isCameraActive = ref(false)
const isRealTimeDetecting = ref(false)
const realTimeInterval = ref(null)

// DOM 引用
const fileInputRef = ref(null)
const videoRef = ref(null)
const canvasRef = ref(null)
const realtimeCanvasRef = ref(null)

// 处理文件上传
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    resultUrl.value = null
    detectionResults.value = null
  }
}

// 清除当前文件
const handleClear = () => {
  selectedFile.value = null
  previewUrl.value = null
  resultUrl.value = null
  detectionResults.value = null
  if (fileInputRef.value) {
    fileInputRef.value.value = ''
  }
}

// YOLO 姿态检测
const handleDetect = async () => {
  if (!selectedFile.value && !isCameraActive.value) {
    alert('请先上传图片或视频，或打开摄像头')
    return
  }

  isDetecting.value = true

  try {
    const formData = new FormData()
    formData.append('image', selectedFile.value)
    formData.append('confidence', '0.25')
    formData.append('iou', '0.45')

    // 调用后端 API
    const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
    const response = await fetch(`${apiUrl}/api/detect`, {
      method: 'POST',
      body: formData
    })

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`)
    }

    const data = await response.json()
    
    if (data.success) {
      // 转换姿态检测返回的数据格式
      const detections = data.detections.map(det => ({
        personId: det.person_id,
        confidence: det.confidence,
        bbox: [det.bbox.x1, det.bbox.y1, det.bbox.x2, det.bbox.y2],
        keypoints: det.keypoints,
        keypointCount: det.keypoint_count
      }))
      
      detectionResults.value = {
        detections: detections,
        processingTime: '实时',
        totalPersons: data.person_count
      }
      
      // 显示结果图像（现在是 base64 格式）
      if (data.result_image) {
        resultUrl.value = data.result_image
      } else {
        resultUrl.value = previewUrl.value
      }
    } else {
      throw new Error(data.error || '姿态检测失败')
    }

  } catch (error) {
    console.error('检测错误:', error)
    alert(`姿态检测失败: ${error.message}`)
  } finally {
    isDetecting.value = false
  }
}

// 打开/关闭摄像头
const toggleCamera = async () => {
  if (isCameraActive.value) {
    if (videoRef.value && videoRef.value.srcObject) {
      const stream = videoRef.value.srcObject
      const tracks = stream.getTracks()
      tracks.forEach(track => track.stop())
      videoRef.value.srcObject = null
    }
    stopRealTimeDetection()
    isCameraActive.value = false
  } else {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { 
          width: { ideal: 1280 },
          height: { ideal: 720 },
          frameRate: { ideal: 60, min: 30 }
        } 
      })
      if (videoRef.value) {
        videoRef.value.srcObject = stream
        videoRef.value.play()
      }
      isCameraActive.value = true
      selectedFile.value = null
      previewUrl.value = null
      resultUrl.value = null
    } catch (error) {
      console.error('无法访问摄像头:', error)
      alert('无法访问摄像头，请确保已授予权限')
    }
  }
}

// 从摄像头捕获图片
const captureFromCamera = () => {
  if (videoRef.value && canvasRef.value) {
    const video = videoRef.value
    const canvas = canvasRef.value
    canvas.width = video.videoWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext('2d')
    ctx.drawImage(video, 0, 0)
    
    canvas.toBlob((blob) => {
      const file = new File([blob], 'camera-capture.jpg', { type: 'image/jpeg' })
      selectedFile.value = file
      previewUrl.value = URL.createObjectURL(file)
      stopRealTimeDetection()
      toggleCamera()
    }, 'image/jpeg')
  }
}

// 实时姿态检测
const startRealTimeDetection = async () => {
  if (!isCameraActive.value) {
    alert('请先打开摄像头')
    return
  }

  isRealTimeDetecting.value = true
  
  const detectFrame = async () => {
    if (!isRealTimeDetecting.value || !videoRef.value || !realtimeCanvasRef.value) {
      return
    }

    try {
      const video = videoRef.value
      const canvas = canvasRef.value
      // 保持高分辨率以充分利用GPU性能
      canvas.width = video.videoWidth
      canvas.height = video.videoHeight
      const ctx = canvas.getContext('2d')
      ctx.drawImage(video, 0, 0)

      // 将画布转换为 Blob，80%质量平衡速度和质量
      const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8))
      const formData = new FormData()
      formData.append('image', blob, 'frame.jpg')
      formData.append('confidence', '0.35')
      formData.append('iou', '0.5')

      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:5000'
      const response = await fetch(`${apiUrl}/api/detect`, {
        method: 'POST',
        body: formData
      })

      if (response.ok) {
        const data = await response.json()
        if (data.success && data.result_image) {
          // 在实时画布上显示检测结果
          const img = new Image()
          img.onload = () => {
            const rtCanvas = realtimeCanvasRef.value
            if (rtCanvas) {
              rtCanvas.width = img.width
              rtCanvas.height = img.height
              const rtCtx = rtCanvas.getContext('2d')
              rtCtx.drawImage(img, 0, 0)
            }
          }
          img.src = data.result_image

          // 更新检测结果
          const detections = data.detections.map(det => ({
            personId: det.person_id,
            confidence: det.confidence,
            keypointCount: det.keypoint_count
          }))
          
          detectionResults.value = {
            detections: detections,
            totalPersons: data.person_count,
            processingTime: '实时'
          }
        }
      }
    } catch (error) {
      console.error('实时检测错误:', error)
    }

    // 继续下一帧检测（RTX 5070 Ti GPU加速，50ms间隔实现极致流畅体验）
    if (isRealTimeDetecting.value) {
      setTimeout(detectFrame, 50) // 每50ms检测一次，约20fps
    }
  }

  detectFrame()
}

const stopRealTimeDetection = () => {
  isRealTimeDetecting.value = false
  if (realTimeInterval.value) {
    clearInterval(realTimeInterval.value)
    realTimeInterval.value = null
  }
}

// 组件卸载时清理
onUnmounted(() => {
  stopRealTimeDetection()
  if (isCameraActive.value && videoRef.value && videoRef.value.srcObject) {
    const stream = videoRef.value.srcObject
    const tracks = stream.getTracks()
    tracks.forEach(track => track.stop())
  }
})

// 下载姿态检测结果到本地
const downloadResult = async () => {
  if (!resultUrl.value) return
  
  try {
    // 如果是 base64 格式，直接下载
    if (resultUrl.value.startsWith('data:')) {
      const link = document.createElement('a')
      link.href = resultUrl.value
      link.download = `yolo_pose_detection_${new Date().getTime()}.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } else {
      // 如果是 URL，先 fetch 再下载
      const response = await fetch(resultUrl.value)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `yolo_pose_detection_${new Date().getTime()}.jpg`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
  } catch (error) {
    console.error('下载失败:', error)
    alert('下载失败，请重试')
  }
}
</script>

<template>
  <div class="app-container">
    
    <!-- 最左侧：模式选择竖状按钮 -->
    <div class="sidebar">
      <div class="logo">🤸</div>
      
      <button @click="mode = 'image'" :class="['mode-btn', { active: mode === 'image' }]" title="图片检测">
        <span class="icon">📷</span>
        <span class="label">图片</span>
      </button>
      
      <button @click="mode = 'video'" :class="['mode-btn', { active: mode === 'video' }]" title="视频检测">
        <span class="icon">🎥</span>
        <span class="label">视频</span>
      </button>
      
      <button @click="mode = 'camera'" :class="['mode-btn', { active: mode === 'camera' }]" title="实时检测">
        <span class="icon">📹</span>
        <span class="label">实时</span>
      </button>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      
      <!-- 左侧：检测画面区域 -->
      <div class="detection-panel">
        <div class="panel-card">
          
          <!-- 标题栏 -->
          <div class="panel-header">
            <h1 class="panel-title">
              <span class="title-icon">📥</span>
              <span>{{ mode === 'camera' ? '摄像头画面' : mode === 'video' ? '视频画面' : '图片画面' }}</span>
            </h1>
          </div>

          <!-- 检测画面显示区 -->
          <div class="display-area">
            
            <!-- 摄像头模式 -->
            <div v-if="mode === 'camera'" class="camera-view">
              <div class="video-container">
                <video ref="videoRef" class="video-element" playsinline v-show="!isRealTimeDetecting" />
                <canvas ref="realtimeCanvasRef" class="video-element" v-show="isRealTimeDetecting" />
                <div v-if="!isCameraActive" class="placeholder">
                  <div class="placeholder-icon">📹</div>
                  <p class="placeholder-text">点击下方按钮启动摄像头</p>
                </div>
                <div v-if="isRealTimeDetecting" class="live-badge">
                  <span class="live-dot"></span>
                  实时检测中
                </div>
              </div>
              <canvas ref="canvasRef" style="display: none" />
            </div>

            <!-- 图片/视频模式 -->
            <div v-else class="file-view">
              <div v-if="!previewUrl" @click="fileInputRef?.click()" class="upload-area">
                <div class="upload-icon">📤</div>
                <p class="upload-title">点击上传{{ mode === 'image' ? '图片' : '视频' }}</p>
                <p class="upload-hint">支持格式: {{ mode === 'image' ? 'JPG, PNG, WebP' : 'MP4, AVI, MOV' }}</p>
              </div>
              <div v-else class="preview-container">
                <img v-if="mode === 'image'" :src="previewUrl" alt="预览" class="preview-element" />
                <video v-else :src="previewUrl" controls class="preview-element" />
              </div>
              <input ref="fileInputRef" type="file" :accept="mode === 'image' ? 'image/*' : 'video/*'" @change="handleFileSelect" class="hidden" />
            </div>
          </div>

          <!-- 底部控制按钮 -->
          <div class="control-buttons">
            <!-- 摄像头模式按钮 -->
            <template v-if="mode === 'camera'">
              <button @click="toggleCamera" :class="['btn', 'btn-primary', isCameraActive ? 'btn-danger' : 'btn-success']">
                <span class="btn-icon">{{ isCameraActive ? '⏹' : '▶️' }}</span>
                <span>{{ isCameraActive ? '关闭摄像头' : '打开摄像头' }}</span>
              </button>
              
              <button v-if="isCameraActive && !isRealTimeDetecting" @click="startRealTimeDetection" class="btn btn-primary btn-purple">
                <span class="btn-icon">🎬</span>
                <span>开始实时检测</span>
              </button>
              
              <button v-if="isRealTimeDetecting" @click="stopRealTimeDetection" class="btn btn-primary btn-orange">
                <span class="btn-icon">⏹</span>
                <span>停止检测</span>
              </button>
            </template>

            <!-- 图片/视频模式按钮 -->
            <template v-else>
              <button @click="fileInputRef?.click()" class="btn btn-primary btn-blue">
                <span class="btn-icon">📁</span>
                <span>{{ previewUrl ? '重新选择' : '打开文件' }}</span>
              </button>
              
              <button @click="handleDetect" :disabled="isDetecting || !selectedFile" :class="['btn', 'btn-primary', 'btn-purple', { 'btn-disabled': isDetecting || !selectedFile }]">
                <span v-if="isDetecting" class="btn-spinner"></span>
                <span v-else class="btn-icon">🚀</span>
                <span>{{ isDetecting ? '检测中...' : '开始检测' }}</span>
              </button>
            </template>
          </div>
        </div>
      </div>

      <!-- 右侧：检测结果区域 -->
      <div class="results-panel">
        <div class="panel-card">
          
          <!-- 标题栏 -->
          <div class="panel-header">
            <h2 class="panel-title">
              <span class="title-icon">🎯</span>
              <span>检测结果</span>
            </h2>
          </div>

          <!-- 结果内容 -->
          <div class="results-content">
            
            <div v-if="!resultUrl && !detectionResults" class="results-placeholder">
              <div class="placeholder-icon">🤸</div>
              <p class="placeholder-text">等待检测结果...</p>
            </div>
            
            <div v-else class="results-data">
              
              <!-- 结果图像 -->
              <div v-if="resultUrl && !isRealTimeDetecting" class="result-image">
                <img :src="resultUrl" alt="检测结果" />
              </div>

              <!-- 下载按钮 -->
              <button v-if="resultUrl && !isRealTimeDetecting" @click="downloadResult" class="btn btn-primary btn-green btn-full">
                <span class="btn-icon">💾</span>
                <span>保存结果</span>
              </button>

              <!-- 统计信息 -->
              <div v-if="detectionResults" class="stats-section">
                <div class="stats-grid">
                  <div class="stat-card stat-blue">
                    <p class="stat-label">检测人数</p>
                    <p class="stat-value">{{ detectionResults.totalPersons }}</p>
                  </div>
                  <div class="stat-card stat-green">
                    <p class="stat-label">状态</p>
                    <p class="stat-value-small">{{ detectionResults.processingTime }}</p>
                  </div>
                </div>

                <!-- 详细信息 -->
                <div class="details-section">
                  <h3 class="details-title">
                    <span class="title-icon">📊</span>
                    <span>姿态详情</span>
                  </h3>
                  <div class="details-list">
                    <div v-for="(detection, index) in detectionResults.detections" :key="index" class="detail-item">
                      <div class="detail-header">
                        <div class="detail-left">
                          <div class="detail-badge">{{ index + 1 }}</div>
                          <span class="detail-name">人物 #{{ detection.personId + 1 }}</span>
                        </div>
                        <div class="detail-right">
                          <div class="confidence-label">置信度</div>
                          <div class="confidence-value">{{ (detection.confidence * 100).toFixed(1) }}%</div>
                        </div>
                      </div>
                      <div class="detail-info">
                        <span class="info-tag">🎯 {{ detection.keypointCount }} 个关键点</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* 主容器 */
.app-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  background: linear-gradient(135deg, #1e293b 0%, #581c87 50%, #1e293b 100%);
  overflow: hidden;
}

/* 侧边栏 */
.sidebar {
  width: 80px;
  min-width: 80px;
  background: linear-gradient(180deg, #4f46e5 0%, #7c3aed 100%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem 0;
  gap: 1rem;
  box-shadow: 4px 0 20px rgba(0, 0, 0, 0.3);
}

.logo {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.mode-btn {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mode-btn:hover {
  transform: scale(1.1);
  background: rgba(255, 255, 255, 0.3);
}

.mode-btn.active {
  background: white;
  transform: scale(1.1);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
}

.mode-btn.active .icon {
  filter: none;
}

.mode-btn .icon {
  font-size: 1.5rem;
}

.mode-btn .label {
  font-size: 0.75rem;
  margin-top: 0.25rem;
  font-weight: 600;
}

.mode-btn.active .label {
  color: #4f46e5;
}

/* 主内容区 */
.main-content {
  flex: 1;
  display: flex;
  gap: 1.5rem;
  padding: 1.5rem;
  overflow: hidden;
}

/* 检测面板和结果面板 */
.detection-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.results-panel {
  width: 420px;
  min-width: 420px;
  display: flex;
  flex-direction: column;
}

.panel-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(10px);
  border-radius: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.3);
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

/* 面板标题 */
.panel-header {
  background: linear-gradient(90deg, rgba(79, 70, 229, 0.8) 0%, rgba(124, 58, 237, 0.8) 100%);
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.panel-title {
  font-size: 1.5rem;
  font-weight: 900;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
}

.title-icon {
  font-size: 1.75rem;
}

/* 显示区域 */
.display-area {
  flex: 1;
  padding: 1.5rem;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.camera-view,
.file-view {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.video-container,
.preview-container {
  flex: 1;
  background: #000;
  border-radius: 12px;
  overflow: hidden;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-element,
.preview-element {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

/* 占位符 */
.placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1f2937 0%, #000 100%);
}

.placeholder-icon {
  font-size: 6rem;
  opacity: 0.5;
  animation: pulse 2s infinite;
}

.placeholder-text {
  font-size: 1.25rem;
  color: rgba(255, 255, 255, 0.6);
  margin-top: 1.5rem;
}

/* 实时检测徽章 */
.live-badge {
  position: absolute;
  top: 1.5rem;
  left: 1.5rem;
  background: #ef4444;
  color: white;
  padding: 0.75rem 1.5rem;
  border-radius: 9999px;
  font-weight: bold;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 10px 30px rgba(239, 68, 68, 0.5);
  animation: pulse 2s infinite;
}

.live-dot {
  width: 12px;
  height: 12px;
  background: white;
  border-radius: 50%;
}

/* 上传区域 */
.upload-area {
  width: 100%;
  height: 100%;
  border: 4px dashed rgba(99, 102, 241, 0.3);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: rgba(99, 102, 241, 0.6);
  background: rgba(255, 255, 255, 0.05);
}

.upload-icon {
  font-size: 6rem;
  opacity: 0.5;
  animation: bounce 2s infinite;
}

.upload-title {
  color: white;
  font-size: 1.875rem;
  font-weight: bold;
  margin-top: 2rem;
  margin-bottom: 0.75rem;
}

.upload-hint {
  color: rgba(255, 255, 255, 0.5);
  font-size: 1.25rem;
}

/* 控制按钮 */
.control-buttons {
  padding: 1.5rem;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.btn {
  padding: 1rem 1.5rem;
  border-radius: 12px;
  font-weight: bold;
  font-size: 1.125rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.75rem;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
}

.btn:hover:not(.btn-disabled) {
  transform: scale(1.05);
}

.btn-icon {
  font-size: 1.875rem;
}

.btn-primary {
  color: white;
}

.btn-success {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.btn-success:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.btn-danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.btn-danger:hover {
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}

.btn-purple {
  background: linear-gradient(135deg, #a855f7 0%, #7c3aed 100%);
}

.btn-purple:hover {
  background: linear-gradient(135deg, #9333ea 0%, #6b21a8 100%);
}

.btn-orange {
  background: linear-gradient(135deg, #f97316 0%, #ea580c 100%);
}

.btn-orange:hover {
  background: linear-gradient(135deg, #ea580c 0%, #c2410c 100%);
}

.btn-blue {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
}

.btn-blue:hover {
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}

.btn-green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.btn-green:hover {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
}

.btn-full {
  grid-column: 1 / -1;
}

.btn-disabled {
  background: #4b5563;
  color: #9ca3af;
  cursor: not-allowed;
  opacity: 0.6;
}

.btn-spinner {
  width: 1.5rem;
  height: 1.5rem;
  border: 4px solid white;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

/* 结果内容 */
.results-content {
  flex: 1;
  padding: 1.5rem;
  overflow-y: auto;
  min-height: 0;
}

.results-placeholder {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.results-data {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-image {
  background: #000;
  border-radius: 12px;
  overflow: hidden;
}

.result-image img {
  width: 100%;
  height: auto;
  display: block;
}

/* 统计卡片 */
.stats-section {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
}

.stat-card {
  padding: 1.25rem;
  border-radius: 12px;
  color: white;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.2);
}

.stat-blue {
  background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
}

.stat-green {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.stat-label {
  font-size: 0.875rem;
  opacity: 0.9;
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 900;
  line-height: 1;
}

.stat-value-small {
  font-size: 1.5rem;
  font-weight: 900;
}

/* 详细信息 */
.details-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 1.25rem;
  backdrop-filter: blur(10px);
}

.details-title {
  color: white;
  font-weight: bold;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
}

.details-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.detail-item {
  background: rgba(255, 255, 255, 0.1);
  padding: 1rem;
  border-radius: 12px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.detail-item:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.2);
}

.detail-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.detail-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.detail-badge {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 900;
  font-size: 1.125rem;
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.3);
}

.detail-name {
  color: white;
  font-weight: bold;
  font-size: 1rem;
}

.detail-right {
  text-align: right;
}

.confidence-label {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.75rem;
  margin-bottom: 0.25rem;
}

.confidence-value {
  color: #10b981;
  font-weight: 900;
  font-size: 1.25rem;
}

.detail-info {
  display: flex;
  gap: 0.5rem;
}

.info-tag {
  background: linear-gradient(135deg, #3b82f6 0%, #4f46e5 100%);
  color: white;
  padding: 0.5rem 0.75rem;
  border-radius: 9999px;
  font-weight: bold;
  font-size: 0.75rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

/* 滚动条样式 */
.custom-scrollbar::-webkit-scrollbar,
.details-list::-webkit-scrollbar,
.results-content::-webkit-scrollbar {
  width: 8px;
}

.custom-scrollbar::-webkit-scrollbar-track,
.details-list::-webkit-scrollbar-track,
.results-content::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb,
.details-list::-webkit-scrollbar-thumb,
.results-content::-webkit-scrollbar-thumb {
  background: linear-gradient(to bottom, #4f46e5, #7c3aed);
  border-radius: 10px;
}

.custom-scrollbar::-webkit-scrollbar-thumb:hover,
.details-list::-webkit-scrollbar-thumb:hover,
.results-content::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(to bottom, #4338ca, #6b21a8);
}

/* 动画 */
@keyframes pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.5;
  }
}

@keyframes bounce {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-20px);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 隐藏元素 */
.hidden {
  display: none;
}

/* 响应式调整 */
@media (max-width: 1280px) {
  .results-panel {
    width: 360px;
    min-width: 360px;
  }
}

@media (max-width: 1024px) {
  .main-content {
    flex-direction: column;
  }
  
  .results-panel {
    width: 100%;
    min-width: 0;
    max-height: 40vh;
  }
}
</style>

<style>
/* 全局样式重置 */
html, body {
  margin: 0 !important;
  padding: 0 !important;
  width: 100%;
  height: 100%;
  overflow: hidden;
}

#app {
  width: 100%;
  height: 100%;
}
</style>