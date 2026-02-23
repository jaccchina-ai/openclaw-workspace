#!/bin/bash
# T01 龙头战法选股运行脚本

set -e

cd "$(dirname "$0")"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 python3"
    exit 1
fi

# 检查依赖
if [ ! -f "requirements.txt" ]; then
    echo "错误: requirements.txt 不存在"
    exit 1
fi

# 检查配置
if [ ! -f "config.yaml" ]; then
    echo "提示: config.yaml 不存在，使用示例配置"
    if [ -f "config.example.yaml" ]; then
        cp config.example.yaml config.yaml
        echo "请编辑 config.yaml 填写实际配置"
        exit 1
    else
        echo "错误: config.example.yaml 也不存在"
        exit 1
    fi
fi

# 安装依赖（可选）
if [ "$1" = "--install" ]; then
    echo "安装Python依赖..."
    pip3 install -r requirements.txt
    exit 0
fi

# 运行主程序
echo "运行龙头战法选股系统 (T01)..."
python3 main.py "$@"