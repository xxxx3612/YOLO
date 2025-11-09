import pytest
from calculator import calculator

def test_calculator_exists():
    """测试计算器函数是否存在"""
    assert callable(calculator)

# 由于calculator函数包含用户输入，我们需要模拟输入进行测试
# 这里只测试函数存在性，如需完整测试需要重构calculator函数以接受参数而不是使用input()