# Linlinegg MCP Calculator Server

[![PyPI version](https://badge.fury.io/py/linlinegg-mcp-calculator-server.svg)](https://badge.fury.io/py/linlinegg-mcp-calculator-server)
[![Python Version](https://img.shields.io/pypi/pyversions/linlinegg-mcp-calculator-server.svg)](https://pypi.org/project/linlinegg-mcp-calculator-server/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

一个简单而强大的 MCP (Model Context Protocol) 服务器，为 AI 应用提供计算器、时间查询和天气查询功能。

## ✨ 特性

- 🧮 **计算器功能**：支持基本四则运算和复杂表达式计算
- ⏰ **时间查询**：获取当前系统时间
- 🌤️ **天气查询**：模拟天气数据查询（可扩展为真实 API）
- 🚀 **即插即用**：一键安装，快速集成到 Cursor、Claude Desktop 等应用
- 🔒 **安全可靠**：表达式计算使用安全沙箱，防止代码注入

## 📦 安装

```bash
pip install linlinegg-mcp-calculator-server
```

或者从源码安装：

```bash
git clone https://github.com/linlinegg/mcp-calculator-server
cd linlinegg-mcp-calculator-server
pip install -e .
```

## 🚀 快速开始

### 在 Cursor 中使用

1. 打开 Cursor 设置中的 MCP 配置文件（通常在 `~/.cursor/mcp.json`）

2. 添加以下配置：

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator",
      "args": [],
      "env": {}
    }
  }
}
```

3. 重启 Cursor

4. 现在 AI 助手可以使用以下功能：
   - "现在几点了？"
   - "帮我计算 123 + 456"
   - "计算表达式 (100 - 5) * 3 + 2"
   - "深圳的天气怎么样？"

### 在 Claude Desktop 中使用

编辑 Claude Desktop 的配置文件：

**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

添加配置：

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator"
    }
  }
}
```

### 命令行测试

直接运行服务器进行测试：

```bash
linlinegg-mcp-calculator
```

或使用 Python 模块：

```bash
python -m linlinegg_mcp_calculator.server
```

## 🛠️ 可用工具

### 1. get_time
获取当前系统时间

**示例**：
```
用户：现在几点了？
AI：调用 get_time() -> "2024-10-24 15:30:45"
```

### 2. calculator
执行基本数学运算

**参数**：
- `a` (float): 第一个数字
- `b` (float): 第二个数字
- `operation` (str): 运算符（add, subtract, multiply, divide）

**示例**：
```
用户：计算 100 除以 5
AI：调用 calculator(100, 5, "divide") -> {"result": 20.0}
```

### 3. eval_expression
计算复杂数学表达式

**参数**：
- `expression` (str): 数学表达式

**示例**：
```
用户：计算 (100 - 5) * 3 + 2
AI：调用 eval_expression("(100-5)*3+2") -> {"result": 287}
```

### 4. weather
查询城市天气（模拟数据）

**参数**：
- `city` (str): 城市名称

**示例**：
```
用户：深圳天气怎么样？
AI：调用 weather("深圳") -> "小雨，温度 22-30°C"
```

支持的城市：北京、上海、深圳、杭州（以及对应的英文名称）

## 📖 开发指南

### 克隆项目

```bash
git clone https://github.com/linlinegg/mcp-calculator-server
cd linlinegg-mcp-calculator-server
```

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest
```

### 代码格式化

```bash
black linlinegg_mcp_calculator/
ruff check linlinegg_mcp_calculator/
```

### 添加新工具

在 `linlinegg_mcp_calculator/server.py` 中添加新的工具函数：

```python
@mcp.tool()
def your_new_tool(param1: str, param2: int) -> dict:
    """
    你的工具描述
    
    Args:
        param1: 参数1描述
        param2: 参数2描述
    
    Returns:
        返回值描述
    """
    # 实现你的逻辑
    return {"result": "..."}
```

## 🔧 高级配置

### 使用特定 Python 环境

如果你在虚拟环境中安装了此包，需要在 MCP 配置中指定完整路径：

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "/path/to/venv/bin/linlinegg-mcp-calculator",
      "args": [],
      "env": {}
    }
  }
}
```

### 添加环境变量

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator",
      "env": {
        "LOG_LEVEL": "DEBUG",
        "WEATHER_API_KEY": "your-api-key"
      }
    }
  }
}
```

## 🌟 扩展建议

这个包是一个很好的起点，你可以扩展它来添加更多功能：

1. **真实天气 API**：集成 OpenWeatherMap、和风天气等真实天气服务
2. **数据库查询**：添加数据库连接和查询功能
3. **文件操作**：添加文件读写、搜索功能
4. **API 调用**：集成第三方 API（翻译、搜索等）
5. **数据分析**：添加数据统计、图表生成等功能

## 📚 相关资源

- [MCP 官方文档](https://modelcontextprotocol.io/)
- [FastMCP 库](https://github.com/jlowin/fastmcp)
- [MCP 服务器示例](https://github.com/modelcontextprotocol/servers)
- [Cursor 文档](https://cursor.sh/)

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 👨‍💻 作者

**Linlinegg**

- GitHub: [@linlinegg](https://github.com/linlinegg)
- Email: your.email@example.com

## 🙏 致谢

- 感谢 [Anthropic](https://www.anthropic.com/) 开发的 Model Context Protocol
- 感谢 [FastMCP](https://github.com/jlowin/fastmcp) 提供的简洁 API

---

⭐ 如果这个项目对你有帮助，请给它一个 Star！

