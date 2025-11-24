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
const isVideoDetecting = ref(false)
const videoDetectionInterval = ref(null)

// DOM 引用
const fileInputRef = ref(null)
const videoRef = ref(null)
const canvasRef = ref(null)
const realtimeCanvasRef = ref(null)
const videoPreviewRef = ref(null)
const videoCanvasRef = ref(null)

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
  // 停止视频检测
  if (isVideoDetecting.value) {
    stopVideoDetection()
  }
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

  // 如果是视频模式，启动逐帧检测
  if (mode.value === 'video') {
    startVideoDetection()
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

// 视频逐帧检测
const startVideoDetection = async () => {
  if (!videoPreviewRef.value || !videoCanvasRef.value) {
    alert('视频元素未准备好')
    return
  }

  const video = videoPreviewRef.value
  const canvas = videoCanvasRef.value
  
  // 等待视频元数据加载
  if (video.readyState < 2) {
    await new Promise(resolve => {
      video.addEventListener('loadedmetadata', resolve, { once: true })
    })
  }
  
  // 初始化画布
  await new Promise(resolve => setTimeout(resolve, 100))
  canvas.width = video.videoWidth || 1280
  canvas.height = video.videoHeight || 720
  
  // 创建临时画布用于帧捕获
  const tempCanvas = document.createElement('canvas')
  
  // 开始播放视频
  video.play()
  isVideoDetecting.value = true
  isDetecting.value = true
  
  const detectFrame = async () => {
    if (!isVideoDetecting.value || !video || video.paused || video.ended) {
      stopVideoDetection()
      return
    }

    try {
      // 从视频捕获当前帧到临时画布
      tempCanvas.width = video.videoWidth
      tempCanvas.height = video.videoHeight
      const tempCtx = tempCanvas.getContext('2d')
      tempCtx.drawImage(video, 0, 0)

      // 将帧转换为 Blob
      const blob = await new Promise(resolve => tempCanvas.toBlob(resolve, 'image/jpeg', 0.8))
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
          // 在画布上显示检测结果
          const img = new Image()
          img.onload = () => {
            if (canvas) {
              const ctx = canvas.getContext('2d')
              ctx.drawImage(img, 0, 0, canvas.width, canvas.height)
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
      console.error('视频检测错误:', error)
    }

    // 继续下一帧检测（50ms间隔）
    if (isVideoDetecting.value) {
      setTimeout(detectFrame, 50)
    }
  }

  detectFrame()
}

const stopVideoDetection = () => {
  isVideoDetecting.value = false
  isDetecting.value = false
  detectionResults.value = null
  if (videoPreviewRef.value) {
    videoPreviewRef.value.pause()
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
  if (isVideoDetecting.value) {
    stopVideoDetection()
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
                <template v-else-if="mode === 'video'">
                  <video ref="videoPreviewRef" :src="previewUrl" class="preview-element" v-show="!isVideoDetecting" />
                  <canvas ref="videoCanvasRef" class="preview-element" v-show="isVideoDetecting" />
                </template>
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
              
              <button v-if="!isVideoDetecting" @click="handleDetect" :disabled="isDetecting || !selectedFile" :class="['btn', 'btn-primary', 'btn-purple', { 'btn-disabled': isDetecting || !selectedFile }]">
                <span v-if="isDetecting && mode === 'image'" class="btn-spinner"></span>
                <span v-else class="btn-icon">🚀</span>
                <span>{{ isDetecting && mode === 'image' ? '检测中...' : '开始检测' }}</span>
              </button>
              
              <button v-if="isVideoDetecting" @click="stopVideoDetection" class="btn btn-primary btn-orange">
                <span class="btn-icon">⏹</span>
                <span>停止检测</span>
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