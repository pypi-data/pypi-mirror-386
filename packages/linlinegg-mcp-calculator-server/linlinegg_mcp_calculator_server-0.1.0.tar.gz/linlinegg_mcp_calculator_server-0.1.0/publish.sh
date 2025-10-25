#!/bin/bash
# 发布脚本 - 自动化构建和发布流程

set -e  # 遇到错误立即退出

echo "🚀 开始发布流程..."
echo ""

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 检查是否安装了必要的工具
echo "📦 检查依赖工具..."
if ! command -v python &> /dev/null; then
    echo -e "${RED}❌ Python 未安装${NC}"
    exit 1
fi

if ! python -m pip show build &> /dev/null; then
    echo -e "${YELLOW}⚠️  build 未安装，正在安装...${NC}"
    pip install build
fi

if ! python -m pip show twine &> /dev/null; then
    echo -e "${YELLOW}⚠️  twine 未安装，正在安装...${NC}"
    pip install twine
fi

echo -e "${GREEN}✅ 依赖检查完成${NC}"
echo ""

# 询问发布类型
echo "请选择发布类型："
echo "1) TestPyPI (测试环境)"
echo "2) PyPI (正式环境)"
read -p "请输入选项 [1/2]: " release_type

# 清理旧的构建文件
echo ""
echo "🧹 清理旧的构建文件..."
rm -rf dist/ build/ *.egg-info
echo -e "${GREEN}✅ 清理完成${NC}"

# 构建包
echo ""
echo "🔨 构建包..."
python -m build
echo -e "${GREEN}✅ 构建完成${NC}"

# 检查包
echo ""
echo "🔍 检查包..."
python -m twine check dist/*
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 包检查失败${NC}"
    exit 1
fi
echo -e "${GREEN}✅ 包检查通过${NC}"

# 显示构建结果
echo ""
echo "📦 构建的文件："
ls -lh dist/
echo ""

# 上传
if [ "$release_type" = "1" ]; then
    echo "📤 上传到 TestPyPI..."
    python -m twine upload --repository testpypi dist/*
    if [ $? -eq 0 ]; then
        echo ""
        echo -e "${GREEN}✅ 上传到 TestPyPI 成功！${NC}"
        echo ""
        echo "测试安装命令："
        echo "pip install --index-url https://test.pypi.org/simple/ linlinegg-mcp-calculator-server"
    fi
elif [ "$release_type" = "2" ]; then
    echo -e "${YELLOW}⚠️  你确定要发布到正式 PyPI 吗？这个操作不可逆！${NC}"
    read -p "请输入 'yes' 确认: " confirm
    if [ "$confirm" = "yes" ]; then
        echo "📤 上传到 PyPI..."
        python -m twine upload dist/*
        if [ $? -eq 0 ]; then
            echo ""
            echo -e "${GREEN}✅ 发布成功！🎉${NC}"
            echo ""
            echo "安装命令："
            echo "pip install linlinegg-mcp-calculator-server"
            echo ""
            echo "查看项目："
            echo "https://pypi.org/project/linlinegg-mcp-calculator-server/"
        fi
    else
        echo -e "${YELLOW}❌ 发布已取消${NC}"
        exit 0
    fi
else
    echo -e "${RED}❌ 无效选项${NC}"
    exit 1
fi

echo ""
echo -e "${GREEN}🎉 完成！${NC}"

