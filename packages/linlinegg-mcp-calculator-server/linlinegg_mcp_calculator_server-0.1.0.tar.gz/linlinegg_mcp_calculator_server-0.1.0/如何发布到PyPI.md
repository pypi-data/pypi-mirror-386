# 📦 如何发布 linlinegg-mcp-calculator-server 到 PyPI

## 🎉 恭喜！你的包已经准备就绪

你的包结构：

```
linlinegg-mcp-calculator-server/
├── linlinegg_mcp_calculator/      # 主程序包
│   ├── __init__.py               # 包初始化
│   └── server.py                 # MCP 服务器主程序
├── pyproject.toml                # 包配置文件（最重要！）
├── README.md                     # 项目说明
├── LICENSE                       # MIT 许可证
├── PUBLISH.md                    # 详细发布指南
├── QUICKSTART.md                 # 快速入门
├── CHANGELOG.md                  # 更新日志
├── MANIFEST.in                   # 打包清单
├── .gitignore                    # Git 忽略文件
└── publish.sh                    # 自动发布脚本
```

## 🚀 三种发布方式

### 方式 1: 使用自动脚本（推荐新手）

```bash
cd /Users/hzl/Desktop/matlab_c/langgraph/examples/linlinegg-mcp-calculator-server
./publish.sh
```

然后按提示选择：
- 选项 1: 发布到 TestPyPI（测试）
- 选项 2: 发布到 PyPI（正式）

### 方式 2: 手动命令（推荐有经验者）

#### 步骤 1: 安装工具

```bash
pip install build twine
```

#### 步骤 2: 构建包

```bash
cd /Users/hzl/Desktop/matlab_c/langgraph/examples/linlinegg-mcp-calculator-server
python -m build
```

#### 步骤 3: 检查包

```bash
python -m twine check dist/*
```

#### 步骤 4a: 测试发布（TestPyPI）

```bash
python -m twine upload --repository testpypi dist/*
```

#### 步骤 4b: 正式发布（PyPI）

```bash
python -m twine upload dist/*
```

### 方式 3: 一键发布

如果你已经配置好了 PyPI token：

```bash
cd /Users/hzl/Desktop/matlab_c/langgraph/examples/linlinegg-mcp-calculator-server

# 清理 + 构建 + 上传 TestPyPI
rm -rf dist/ && python -m build && python -m twine upload --repository testpypi dist/*

# 正式发布
rm -rf dist/ && python -m build && python -m twine upload dist/*
```

## 📝 发布前必读

### 1. 注册 PyPI 账号

访问这两个网站注册账号：

- **TestPyPI** (测试环境): https://test.pypi.org/account/register/
- **PyPI** (正式环境): https://pypi.org/account/register/

### 2. 创建 API Token

登录后：
1. 访问账户设置
2. 找到 "API tokens" 部分
3. 点击 "Add API token"
4. 选择 "Entire account" 权限
5. 复制生成的 token（只显示一次！）

### 3. 配置 PyPI 认证

创建 `~/.pypirc` 文件：

```bash
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-你的正式token

[testpypi]
username = __token__
password = pypi-你的测试token
repository = https://test.pypi.org/legacy/
EOF
```

**重要：** 设置文件权限：
```bash
chmod 600 ~/.pypirc
```

### 4. 修改个人信息（可选）

编辑 `pyproject.toml`，更新：

```toml
[project]
authors = [
    {name = "你的名字", email = "你的邮箱@example.com"}
]
```

编辑 `linlinegg_mcp_calculator/__init__.py`：

```python
__author__ = "你的名字"
__email__ = "你的邮箱@example.com"
```

## 🧪 测试流程

### 1. 先在 TestPyPI 测试

```bash
# 构建
python -m build

# 上传到测试环境
python -m twine upload --repository testpypi dist/*
```

### 2. 测试安装

```bash
# 从 TestPyPI 安装
pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ linlinegg-mcp-calculator-server

# 测试运行
linlinegg-mcp-calculator

# 测试导入
python -c "from linlinegg_mcp_calculator import main; print('成功！')"
```

### 3. 确认无误后发布到正式 PyPI

```bash
# 清理
rm -rf dist/

# 重新构建
python -m build

# 上传到正式 PyPI
python -m twine upload dist/*
```

## ✅ 发布成功后

### 查看你的包

访问：https://pypi.org/project/linlinegg-mcp-calculator-server/

### 任何人都可以安装

```bash
pip install linlinegg-mcp-calculator-server
```

### 在 Cursor 中配置

```json
{
  "mcpServers": {
    "linlinegg-calculator": {
      "command": "linlinegg-mcp-calculator"
    }
  }
}
```

## 🔄 发布新版本

### 1. 更新版本号

编辑 `pyproject.toml`:
```toml
version = "0.2.0"  # 从 0.1.0 升级
```

编辑 `linlinegg_mcp_calculator/__init__.py`:
```python
__version__ = "0.2.0"
```

### 2. 更新 CHANGELOG.md

记录你的更改。

### 3. 重新构建和发布

```bash
rm -rf dist/
python -m build
python -m twine upload dist/*
```

### 4. 创建 Git Tag（推荐）

```bash
git add .
git commit -m "Release v0.2.0"
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main --tags
```

## ⚠️ 常见错误

### 错误 1: 包名已存在

```
HTTPError: 403 Forbidden
The name 'linlinegg-mcp-calculator-server' is already in use.
```

**解决方案**：
- 选择不同的包名（在 `pyproject.toml` 中修改 `name` 字段）
- 或者联系 PyPI 管理员

### 错误 2: 版本号重复

```
HTTPError: 400 Bad Request
File already exists.
```

**解决方案**：
- 更新版本号（必须比之前高）
- PyPI 不允许覆盖已发布的版本

### 错误 3: README 格式错误

```
The description failed to render for the following reason:
...
```

**解决方案**：
- 检查 README.md 的 Markdown 语法
- 使用 `python -m twine check dist/*` 检查

### 错误 4: 认证失败

```
HTTPError: 403 Forbidden
Invalid or non-existent authentication information.
```

**解决方案**：
- 检查 `~/.pypirc` 文件是否正确
- 确认 API token 有效
- 重新生成 token

## 📊 版本号规范

遵循语义化版本（SemVer）：

- **0.1.0** → 初始版本
- **0.1.1** → Bug 修复
- **0.2.0** → 新增功能
- **1.0.0** → 首个稳定版本
- **2.0.0** → 重大更新（不兼容旧版）

## 🎯 发布检查清单

发布前确认：

- [ ] 代码已测试
- [ ] 文档已更新
- [ ] 版本号已更新
- [ ] CHANGELOG.md 已更新
- [ ] 在 TestPyPI 测试成功
- [ ] .pypirc 已配置
- [ ] 已安装 build 和 twine
- [ ] README.md 无格式错误
- [ ] LICENSE 文件存在

## 💡 高级技巧

### 使用 GitHub Actions 自动发布

创建 `.github/workflows/publish.yml`：

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build and publish
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: |
        python -m build
        twine upload dist/*
```

### 本地测试安装

```bash
# 从本地构建安装
pip install dist/linlinegg_mcp_calculator_server-0.1.0-py3-none-any.whl

# 或从源码安装
pip install -e .
```

## 🔗 有用的资源

- [PyPI 官网](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Python 打包指南](https://packaging.python.org/)
- [语义化版本](https://semver.org/lang/zh-CN/)
- [Twine 文档](https://twine.readthedocs.io/)

## 🆘 需要帮助？

- 查看 [PUBLISH.md](PUBLISH.md) 了解更多细节
- 查看 [QUICKSTART.md](QUICKSTART.md) 快速开始
- [提交 Issue](https://github.com/linlinegg/mcp-calculator-server/issues)

---

**准备好了吗？运行发布脚本开始吧！** 🚀

```bash
cd /Users/hzl/Desktop/matlab_c/langgraph/examples/linlinegg-mcp-calculator-server
./publish.sh
```

祝发布顺利！🎉

