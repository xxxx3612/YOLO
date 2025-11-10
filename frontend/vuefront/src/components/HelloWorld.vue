<script setup>
import { ref } from 'vue'
import axios from 'axios'

const num1 = ref('')
const num2 = ref('')
const operation = ref('+')
const result = ref(null)
const error = ref(null)

const calculate = async () => {
  error.value = null
  result.value = null
  
  try {
    //const response = await axios.post('http://127.0.0.1:5000/api/calculate', {
    const response = await axios.post('https://yolo-cp1y.onrender.com/api/calculate', {
      num1: num1.value,
      num2: num2.value,
      op: operation.value
    })
    result.value = response.data.result
  } catch (err) {
    error.value = err.response?.data?.error || '计算失败，请重试'
    console.error('Error:', err)
  }
}

const clear = () => {
  num1.value = ''
  num2.value = ''
  operation.value = '+'
  result.value = null
  error.value = null
}
</script>

<template>
  <div class="calculator">
    <h1>Vue 计算器</h1>
    
    <div class="calculator-grid">
      <div class="input-group">
        <input 
          type="number" 
          v-model="num1" 
          placeholder="第一个数字"
          class="number-input"
        />
        
        <select v-model="operation" class="operation-select">
          <option value="+">+</option>
          <option value="-">-</option>
          <option value="*">×</option>
          <option value="/">÷</option>
        </select>
        
        <input 
          type="number" 
          v-model="num2" 
          placeholder="第二个数字"
          class="number-input"
        />
      </div>

      <div class="button-group">
        <button @click="calculate" class="calc-button">计算</button>
        <button @click="clear" class="clear-button">清除</button>
      </div>

      <div v-if="result !== null" class="result">
        结果: {{ result }}
      </div>
      
      <div v-if="error" class="error">
        {{ error }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.calculator {
  max-width: 500px;
  margin: 0 auto;
  padding: 20px;
  text-align: center;
}

.calculator-grid {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  gap: 10px;
  justify-content: center;
  align-items: center;
}

.number-input {
  width: 120px;
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.operation-select {
  padding: 10px;
  font-size: 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  background-color: white;
}

.button-group {
  display: flex;
  gap: 10px;
  justify-content: center;
}

.calc-button, .clear-button {
  padding: 10px 20px;
  font-size: 16px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.3s;
}

.calc-button {
  background-color: #4CAF50;
  color: white;
}

.clear-button {
  background-color: #f44336;
  color: white;
}

.calc-button:hover {
  background-color: #45a049;
}

.clear-button:hover {
  background-color: #da190b;
}

.result {
  font-size: 24px;
  font-weight: bold;
  color: #2c3e50;
}

.error {
  color: #f44336;
  font-size: 16px;
}
</style>
