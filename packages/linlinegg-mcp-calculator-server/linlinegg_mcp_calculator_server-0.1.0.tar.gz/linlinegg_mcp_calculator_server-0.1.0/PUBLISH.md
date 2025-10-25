# 发布指南

本文档介绍如何将 `linlinegg-mcp-calculator-server` 发布到 PyPI。

## 📋 发布前准备

### 1. 安装构建工具

```bash
pip install build twine
```

### 2. 注册 PyPI 账号

- 访问 [PyPI](https://pypi.org/account/register/)
- 注册一个账号
- **重要**：启用双因素认证（2FA）
- 创建 API Token：[https://pypi.org/manage/account/token/](https://pypi.org/manage/account/token/)

### 3. 配置 PyPI Token

创建 `~/.pypirc` 文件：

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-your-api-token-here

[testpypi]
username = __token__
password = pypi-your-test-api-token-here
repository = https://test.pypi.org/legacy/
```

**安全提示**：不要将此文件提交到 Git！

## 🧪 测试发布（推荐）

先发布到 TestPyPI 进行测试：

### 1. 注册 TestPyPI 账号

- 访问 [TestPyPI](https://test.pypi.org/account/register/)
- 创建 API Token

### 2. 构建包

```bash
cd /Users/hzl/Desktop/matlab_c/langgraph/examples/linlinegg-mcp-calculator-server
python -m build
```

这会在 `dist/` 目录下生成：
- `linlinegg_mcp_calculator_server-0.1.0.tar.gz` (源码包)
- `linlinegg_mcp_calculator_server-0.1.0-py3-none-any.whl` (wheel 包)

### 3. 上传到 TestPyPI

```bash
python -m twine upload --repository testpypi dist/*
```

### 4. 测试安装

```bash
pip install --index-url https://test.pypi.org/simple/ linlinegg-mcp-calculator-server
```

### 5. 测试运行

```bash
linlinegg-mcp-calculator
```

## 🚀 正式发布到 PyPI

### 1. 更新版本号

编辑 `pyproject.toml` 和 `linlinegg_mcp_calculator/__init__.py`，更新版本号：

```toml
version = "0.1.0"  # 改为新版本号
```

```python
__version__ = "0.1.0"  # 改为新版本号
```

### 2. 清理旧的构建文件

```bash
rm -rf dist/ build/ *.egg-info
```

### 3. 重新构建

```bash
python -m build
```

### 4. 检查包

```bash
python -m twine check dist/*
```

### 5. 上传到 PyPI

```bash
python -m twine upload dist/*
```

### 6. 验证发布

访问：https://pypi.org/project/linlinegg-mcp-calculator-server/

### 7. 测试安装

```bash
pip install linlinegg-mcp-calculator-server
```

## 📝 发布检查清单

发布前请确认：

- [ ] 代码已经过充分测试
- [ ] README.md 文档完整且准确
- [ ] 版本号已更新（遵循 [语义化版本](https://semver.org/)）
- [ ] LICENSE 文件存在
- [ ] 所有依赖已在 pyproject.toml 中声明
- [ ] 在 TestPyPI 上测试成功
- [ ] Git 仓库已提交所有更改
- [ ] 创建了 Git tag（如 `v0.1.0`）

## 🔄 更新已发布的包

### 1. 更新代码和版本号

```bash
# 修改代码
# 更新版本号（必须比之前的版本高）
```

### 2. 创建 Git Tag

```bash
git add .
git commit -m "Release v0.2.0"
git tag -a v0.2.0 -m "Release version 0.2.0"
git push origin main --tags
```

### 3. 重新构建和发布

```bash
rm -rf dist/
python -m build
python -m twine upload dist/*
```

## 🛠️ 使用自动化脚本发布

我们提供了一个快捷发布脚本：

```bash
chmod +x publish.sh
./publish.sh
```

## 📊 版本号规范

遵循 [语义化版本](https://semver.org/) (SemVer)：

- **主版本号 (MAJOR)**：不兼容的 API 修改
- **次版本号 (MINOR)**：向下兼容的功能性新增
- **修订号 (PATCH)**：向下兼容的问题修正

示例：
- `0.1.0` → 初始版本
- `0.1.1` → Bug 修复
- `0.2.0` → 添加新功能
- `1.0.0` → 首个稳定版本

## ❌ 常见问题

### 问题 1: 包名已存在

**错误**：`The name 'linlinegg-mcp-calculator-server' is already in use.`

**解决**：选择一个不同的包名，在 `pyproject.toml` 中修改 `name` 字段。

### 问题 2: 版本号冲突

**错误**：`File already exists`

**解决**：确保新版本号高于已发布的所有版本。PyPI 不允许重新上传相同版本。

### 问题 3: README 渲染错误

**解决**：
1. 确保 README.md 格式正确
2. 运行 `python -m twine check dist/*` 检查
3. 在 TestPyPI 上预览

### 问题 4: 导入失败

**解决**：
1. 检查包结构是否正确
2. 确保 `__init__.py` 存在
3. 验证 `pyproject.toml` 中的 `packages` 配置

## 🔗 有用的链接

- [PyPI](https://pypi.org/)
- [TestPyPI](https://test.pypi.org/)
- [Python 打包指南](https://packaging.python.org/)
- [Twine 文档](https://twine.readthedocs.io/)
- [Hatchling 文档](https://hatch.pypa.io/)

## 💡 提示

1. **始终先在 TestPyPI 测试**：避免在正式环境出错
2. **使用 Git Tags**：为每个发布创建标签，方便版本管理
3. **编写 CHANGELOG**：记录每个版本的更改
4. **自动化发布**：使用 GitHub Actions 等 CI/CD 工具
5. **保护 API Token**：不要将 token 提交到代码仓库

---

发布愉快！🎉

