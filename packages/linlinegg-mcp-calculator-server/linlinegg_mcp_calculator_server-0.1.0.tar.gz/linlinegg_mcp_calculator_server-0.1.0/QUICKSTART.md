# 快速入门指南

## 🎯 5 分钟快速上手

### 步骤 1: 安装包

```bash
pip install linlinegg-mcp-calculator-server
```

### 步骤 2: 配置 Cursor

编辑 `~/.cursor/mcp.json`：

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator"
    }
  }
}
```

如果你使用虚拟环境（如 conda）：

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "/opt/anaconda3/envs/your-env/bin/linlinegg-mcp-calculator"
    }
  }
}
```

### 步骤 3: 重启 Cursor

关闭并重新打开 Cursor。

### 步骤 4: 测试

在 Cursor 的 AI 聊天中尝试：

```
现在几点了？
帮我计算 123 + 456
计算表达式 (100 - 5) * 3 + 2
深圳的天气怎么样？
```

## ✅ 验证安装

### 方法 1: 命令行测试

```bash
linlinegg-mcp-calculator
```

如果看到服务器启动，说明安装成功！（按 Ctrl+C 退出）

### 方法 2: Python 测试

```bash
python -c "from linlinegg_mcp_calculator import main; print('安装成功！')"
```

### 方法 3: 检查版本

```bash
pip show linlinegg-mcp-calculator-server
```

## 🔧 常见配置

### macOS 用户

Cursor 配置文件位置：
```bash
~/.cursor/mcp.json
```

### Windows 用户

Cursor 配置文件位置：
```
%USERPROFILE%\.cursor\mcp.json
```

### Linux 用户

Cursor 配置文件位置：
```bash
~/.cursor/mcp.json
```

## 📖 示例对话

### 示例 1: 时间查询
```
👤 用户: 现在几点了？
🤖 AI: [调用 get_time()] 现在是 2024-10-24 15:30:45
```

### 示例 2: 基本计算
```
👤 用户: 帮我算一下 1234 * 567
🤖 AI: [调用 calculator(1234, 567, "multiply")] 
      结果是 699,678
```

### 示例 3: 表达式计算
```
👤 用户: 计算 (100-5)*3+2
🤖 AI: [调用 eval_expression("(100-5)*3+2")]
      表达式 (100-5)*3+2 的结果是 287
```

### 示例 4: 天气查询
```
👤 用户: 北京今天天气怎么样？
🤖 AI: [调用 weather("北京")]
      北京：晴天，温度 15-25°C
```

## ❓ 常见问题

### Q: 为什么 MCP 服务器显示"未连接"？

A: 可能的原因：
1. 包未正确安装 → 运行 `pip install linlinegg-mcp-calculator-server`
2. Python 路径不对 → 使用完整路径（见上方配置示例）
3. 未重启 Cursor → 重启 Cursor

### Q: 如何找到虚拟环境的 Python 路径？

A: 
```bash
# Conda
conda env list
# 路径通常是: /opt/anaconda3/envs/环境名/bin/linlinegg-mcp-calculator

# venv
which python
# 替换 python 为 linlinegg-mcp-calculator
```

### Q: 可以在 Claude Desktop 中使用吗？

A: 可以！配置文件位置：
- **macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

配置内容相同：
```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator"
    }
  }
}
```

### Q: 如何卸载？

A:
```bash
pip uninstall linlinegg-mcp-calculator-server
```

然后从 `~/.cursor/mcp.json` 中删除相关配置。

## 🚀 下一步

- 📚 查看 [完整文档](README.md)
- 🔧 了解 [发布流程](PUBLISH.md)
- 📝 查看 [更新日志](CHANGELOG.md)
- 🌟 给项目点个 Star！

---

遇到问题？[提交 Issue](https://github.com/linlinegg/mcp-calculator-server/issues)

