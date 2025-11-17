<script setup>
import { ref } from 'vue'

// 状态管理
const mode = ref('image')
const selectedFile = ref(null)
const previewUrl = ref(null)
const resultUrl = ref(null)
const isDetecting = ref(false)
const detectionResults = ref(null)
const isCameraActive = ref(false)

// DOM 引用
const fileInputRef = ref(null)
const videoRef = ref(null)
const canvasRef = ref(null)

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

// YOLO 检测
const handleDetect = async () => {
  if (!selectedFile.value && !isCameraActive.value) {
    alert('请先上传图片或视频，或打开摄像头')
    return
  }

  isDetecting.value = true

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)

    // 模拟延迟
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    // 模拟结果
    const mockResults = {
      detections: [
        { class: '人', confidence: 0.95, bbox: [100, 150, 200, 350] },
        { class: '汽车', confidence: 0.88, bbox: [300, 200, 450, 320] },
        { class: '狗', confidence: 0.92, bbox: [500, 250, 600, 380] }
      ],
      processingTime: '1.2s',
      totalObjects: 3
    }
    
    detectionResults.value = mockResults
    resultUrl.value = previewUrl.value

  } catch (error) {
    console.error('检测错误:', error)
    alert('检测失败，请重试')
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
    isCameraActive.value = false
  } else {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 640, height: 480 } 
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
      toggleCamera()
    }, 'image/jpeg')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6">
    <div class="max-w-7xl mx-auto">
      
      <div class="text-center mb-8">
        <h1 class="text-4xl font-bold text-gray-800 mb-2">🎯 YOLO 目标识别系统</h1>
        <p class="text-gray-600">上传图片或视频，实时识别物体</p>
      </div>

      <div class="bg-white rounded-lg shadow-lg p-6 mb-6">
        <h2 class="text-xl font-semibold mb-4 text-gray-700">选择输入模式</h2>
        <div class="flex gap-4">
          <button @click="mode = 'image'" :class="['flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-lg font-medium transition-all', mode === 'image' ? 'bg-blue-500 text-white shadow-md' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']">
            📷 图片识别
          </button>
          <button @click="mode = 'video'" :class="['flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-lg font-medium transition-all', mode === 'video' ? 'bg-blue-500 text-white shadow-md' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']">
            🎥 视频识别
          </button>
          <button @click="mode = 'camera'" :class="['flex-1 flex items-center justify-center gap-2 py-4 px-6 rounded-lg font-medium transition-all', mode === 'camera' ? 'bg-blue-500 text-white shadow-md' : 'bg-gray-100 text-gray-700 hover:bg-gray-200']">
            📹 摄像头识别
          </button>
        </div>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        
        <div class="bg-white rounded-lg shadow-lg p-6">
          <h2 class="text-xl font-semibold mb-4 text-gray-700">{{ mode === 'camera' ? '摄像头预览' : '输入源' }}</h2>

          <div v-if="mode === 'camera'">
            <div class="relative bg-gray-900 rounded-lg overflow-hidden mb-4" style="aspect-ratio: 4/3">
              <video ref="videoRef" class="w-full h-full object-cover" playsinline />
              <div v-if="!isCameraActive" class="absolute inset-0 flex items-center justify-center text-white">
                <div class="text-center">
                  <div class="text-6xl mb-2">📹</div>
                  <p>点击下方按钮打开摄像头</p>
                </div>
              </div>
            </div>
            <canvas ref="canvasRef" style="display: none" />
            <div class="flex gap-2">
              <button @click="toggleCamera" :class="['flex-1 flex items-center justify-center gap-2 py-3 px-4 rounded-lg font-medium transition-all', isCameraActive ? 'bg-red-500 hover:bg-red-600 text-white' : 'bg-green-500 hover:bg-green-600 text-white']">
                {{ isCameraActive ? '⏹ 关闭摄像头' : '▶️ 打开摄像头' }}
              </button>
              <button v-if="isCameraActive" @click="captureFromCamera" class="flex-1 flex items-center justify-center gap-2 py-3 px-4 bg-blue-500 hover:bg-blue-600 text-white rounded-lg font-medium transition-all">
                📸 拍照
              </button>
            </div>
          </div>

          <div v-else>
            <div v-if="!previewUrl">
              <div @click="fileInputRef?.click()" class="border-4 border-dashed border-gray-300 rounded-lg p-12 text-center cursor-pointer hover:border-blue-400 hover:bg-blue-50 transition-all">
                <div class="text-6xl mb-4">📤</div>
                <p class="text-gray-600 mb-2">点击上传{{ mode === 'image' ? '图片' : '视频' }}</p>
                <p class="text-sm text-gray-500">支持格式: {{ mode === 'image' ? 'JPG, PNG, WebP' : 'MP4, AVI, MOV' }}</p>
              </div>
            </div>
            <div v-else>
              <div class="relative bg-gray-100 rounded-lg overflow-hidden mb-4">
                <img v-if="mode === 'image'" :src="previewUrl" alt="预览" class="w-full h-auto max-h-96 object-contain mx-auto" />
                <video v-else :src="previewUrl" controls class="w-full h-auto max-h-96 object-contain mx-auto" />
              </div>
              <div class="flex gap-2">
                <button @click="fileInputRef?.click()" class="flex-1 flex items-center justify-center gap-2 py-2 px-4 bg-gray-200 hover:bg-gray-300 text-gray-700 rounded-lg font-medium transition-all">
                  🔄 重新上传
                </button>
                <button @click="handleClear" class="flex items-center justify-center gap-2 py-2 px-4 bg-red-500 hover:bg-red-600 text-white rounded-lg font-medium transition-all">
                  🗑️ 清除
                </button>
              </div>
            </div>
            <input ref="fileInputRef" type="file" :accept="mode === 'image' ? 'image/*' : 'video/*'" @change="handleFileSelect" class="hidden" />
          </div>

          <button @click="handleDetect" :disabled="isDetecting || (!selectedFile && !isCameraActive)" :class="['w-full mt-6 py-4 px-6 rounded-lg font-bold text-lg transition-all', isDetecting || (!selectedFile && !isCameraActive) ? 'bg-gray-300 text-gray-500 cursor-not-allowed' : 'bg-gradient-to-r from-blue-500 to-indigo-600 hover:from-blue-600 hover:to-indigo-700 text-white shadow-lg']">
            <span v-if="isDetecting" class="flex items-center justify-center gap-2">
              <div class="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin" />
              检测中...
            </span>
            <span v-else>🚀 开始检测</span>
          </button>
        </div>

        <div class="bg-white rounded-lg shadow-lg p-6">
          <h2 class="text-xl font-semibold mb-4 text-gray-700">检测结果</h2>
          
          <div v-if="!resultUrl && !detectionResults" class="h-full flex items-center justify-center text-gray-400">
            <div class="text-center">
              <div class="text-6xl mb-4">🎯</div>
              <p>等待检测结果...</p>
            </div>
          </div>
          
          <div v-else>
            <div v-if="resultUrl" class="bg-gray-100 rounded-lg overflow-hidden mb-4">
              <img :src="resultUrl" alt="检测结果" class="w-full h-auto max-h-96 object-contain mx-auto" />
            </div>

            <div v-if="detectionResults" class="space-y-4">
              <div class="grid grid-cols-2 gap-4">
                <div class="bg-blue-50 p-4 rounded-lg">
                  <p class="text-sm text-gray-600">检测到的物体</p>
                  <p class="text-2xl font-bold text-blue-600">{{ detectionResults.totalObjects }}</p>
                </div>
                <div class="bg-green-50 p-4 rounded-lg">
                  <p class="text-sm text-gray-600">处理时间</p>
                  <p class="text-2xl font-bold text-green-600">{{ detectionResults.processingTime }}</p>
                </div>
              </div>

              <div>
                <h3 class="font-semibold text-gray-700 mb-2">检测详情：</h3>
                <div class="space-y-2 max-h-64 overflow-y-auto">
                  <div v-for="(detection, index) in detectionResults.detections" :key="index" class="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-all">
                    <div class="flex items-center gap-3">
                      <div class="w-8 h-8 bg-blue-500 text-white rounded-full flex items-center justify-center font-bold">{{ index + 1 }}</div>
                      <span class="font-medium text-gray-700">{{ detection.class }}</span>
                    </div>
                    <div class="text-right">
                      <div class="text-sm text-gray-600">置信度</div>
                      <div class="font-bold text-green-600">{{ (detection.confidence * 100).toFixed(1) }}%</div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div class="mt-6 bg-white rounded-lg shadow-lg p-6">
        <h3 class="text-lg font-semibold mb-3 text-gray-700">💡 使用说明</h3>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm text-gray-600">
          <div class="flex gap-3">
            <div class="text-2xl">1️⃣</div>
            <div><strong>选择模式：</strong>根据需求选择图片、视频或摄像头识别</div>
          </div>
          <div class="flex gap-3">
            <div class="text-2xl">2️⃣</div>
            <div><strong>上传文件：</strong>点击上传区域选择要识别的文件</div>
          </div>
          <div class="flex gap-3">
            <div class="text-2xl">3️⃣</div>
            <div><strong>查看结果：</strong>点击"开始检测"查看识别结果和详细信息</div>
          </div>
        </div>
        
        <div class="mt-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p class="text-sm text-yellow-800">
            <strong>⚠️ 开发提示：</strong>当前为演示模式，检测结果为模拟数据。实际使用时，请在 <code class="bg-yellow-100 px-1 rounded">handleDetect</code> 函数中替换为真实的后端 API 调用。
          </p>
        </div>
      </div>
      
    </div>
  </div>
</template>

<style scoped>
</style>