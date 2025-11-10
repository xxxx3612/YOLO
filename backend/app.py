from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calculator import Calculator

app = Flask(__name__)
CORS(app)

@app.route('/api/calculate', methods=['POST'])
def calculate():
    print("收到计算请求")
    data = request.json
    print(f"接收到的数据: {data}")
    num1 = data.get('num1')
    num2 = data.get('num2')
    op = data.get('op')
    calc = Calculator()
    calc.number_press(str(num1))
    calc.operation_press(op)
    calc.number_press(str(num2))
    result = calc.get_result()
    return jsonify({'result': result})

if __name__ == '__main__':
    print("正在启动 Flask 服务器...")
    print("API 端点: http://127.0.0.1:5000/api/calculate")
    app.run(debug=True, host='127.0.0.1', port=5000)