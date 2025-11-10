from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from calculator import Calculator

app = Flask(__name__)
CORS(app)


@app.route("/api/calculate", methods=["POST"])
def calculate():
    print("收到计算请求")
    data = request.json
    print(f"接收到的数据: {data}")
    num1 = data.get("num1")
    num2 = data.get("num2")
    op = data.get("op")
    calc = Calculator()
    calc.number_press(str(num1))
    calc.operation_press(op)
    calc.number_press(str(num2))
    result = calc.get_result()
    return jsonify({"result": result})


@app.route("/")
def home():
    return "Flask 后端运行正常！"


@app.route("/favicon.ico")
def favicon():
    return app.send_static_file("favicon.ico")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # 获取端口
    app.run(host="0.0.0.0", port=port)  # 绑定到 0.0.0.0
