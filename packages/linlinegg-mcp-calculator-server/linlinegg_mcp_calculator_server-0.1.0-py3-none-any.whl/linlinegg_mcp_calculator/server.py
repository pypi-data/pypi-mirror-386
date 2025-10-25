#!/usr/bin/env python3
"""
Linlinegg MCP Calculator Server - 提供计算器、时间和天气查询功能

这是一个基于 FastMCP 的 MCP 服务器示例，可以被 Cursor、Claude Desktop 等支持 MCP 的应用调用。
"""

from datetime import datetime
from mcp.server.fastmcp import FastMCP

# 创建 FastMCP 服务器实例
mcp = FastMCP("linlinegg-calculator-server")


@mcp.tool()
def get_time() -> str:
    """获取当前时间"""
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")


@mcp.tool()
def calculator(a: float, b: float, operation: str) -> dict:
    """
    执行简单的数学计算
    
    Args:
        a: 第一个数字
        b: 第二个数字
        operation: 运算符 (add, subtract, multiply, divide)
    
    Returns:
        包含计算结果的字典
    """
    if operation == "add":
        result = a + b
    elif operation == "subtract":
        result = a - b
    elif operation == "multiply":
        result = a * b
    elif operation == "divide":
        if b == 0:
            raise ValueError("除数不能为0")
        result = a / b
    else:
        raise ValueError(f"未知运算符: {operation}")
    
    return {
        "operation": operation,
        "a": a,
        "b": b,
        "result": result
    }


@mcp.tool()
def eval_expression(expression: str) -> dict:
    """
    计算数学表达式
    
    Args:
        expression: 数学表达式，如 "100-5*5.5+2"
    
    Returns:
        包含表达式和结果的字典
    """
    # 安全地计算表达式（仅允许数学运算）
    allowed_chars = set("0123456789+-*/(). ")
    if not all(c in allowed_chars for c in expression):
        raise ValueError("表达式包含非法字符")
    
    try:
        result = eval(expression, {"__builtins__": {}}, {})
        return {
            "expression": expression,
            "result": result
        }
    except Exception as e:
        raise ValueError(f"计算错误: {e}")


@mcp.tool()
def weather(city: str) -> str:
    """
    获取城市天气（模拟）
    
    Args:
        city: 城市名称
    
    Returns:
        天气信息
    """
    # 模拟天气数据
    weather_data = {
        "北京": "晴天，温度 15-25°C",
        "上海": "多云，温度 18-28°C",
        "深圳": "小雨，温度 22-30°C",
        "杭州": "阴天，温度 16-26°C",
        "Beijing": "Sunny, 15-25°C",
        "Shanghai": "Cloudy, 18-28°C",
        "Shenzhen": "Light rain, 22-30°C",
        "Hangzhou": "Overcast, 16-26°C"
    }
    
    return weather_data.get(city, f"{city}的天气信息暂无数据 / Weather data not available for {city}")


def main():
    """主入口函数"""
    mcp.run()


if __name__ == "__main__":
    main()

