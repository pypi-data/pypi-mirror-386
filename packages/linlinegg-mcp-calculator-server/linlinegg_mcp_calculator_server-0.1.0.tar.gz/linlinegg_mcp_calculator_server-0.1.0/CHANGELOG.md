# 更新日志

所有重要的更改都将记录在此文件中。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。

## [未发布]

### 计划中
- 集成真实天气 API
- 添加更多数学函数（三角函数、对数等）
- 支持单位转换
- 添加货币汇率查询

## [0.1.0] - 2024-10-24

### 新增
- ✨ 初始版本发布
- 🧮 基本计算器功能（加减乘除）
- 📐 数学表达式计算
- ⏰ 时间查询功能
- 🌤️ 天气查询功能（模拟数据）
- 📚 完整的文档和使用说明
- 🚀 支持 Cursor 和 Claude Desktop
- 🔧 命令行工具 `linlinegg-mcp-calculator`

### 技术栈
- FastMCP 1.0.0+
- Python 3.8+
- MIT 许可证

---

## 版本说明

### [0.1.0] - 初始版本
这是第一个公开发布的版本，提供了基础的 MCP 服务器功能。

**主要功能：**
- 计算器工具
- 时间查询
- 天气查询（模拟）

**使用方式：**
```bash
pip install linlinegg-mcp-calculator-server
linlinegg-mcp-calculator
```

**配置示例：**
```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator"
    }
  }
}
```

---

[未发布]: https://github.com/linlinegg/mcp-calculator-server/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/linlinegg/mcp-calculator-server/releases/tag/v0.1.0

