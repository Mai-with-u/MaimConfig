#!/bin/bash

# MaiMBot API 启动脚本

echo "🚀 启动 MaiMBot API Server..."

# 检查Python环境
if ! command -v python &> /dev/null; then
    echo "❌ 错误: Python 未安装"
    exit 1
fi

# 检查虚拟环境
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  警告: 未检测到虚拟环境，建议使用虚拟环境"
fi

# 安装依赖
echo "📦 安装依赖..."
pip install -r requirements.txt

# 检查环境配置文件
if [[ ! -f .env ]]; then
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo "⚠️  请编辑 .env 文件配置数据库连接信息"
fi

# 启动服务
echo "🎯 启动API服务..."
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

echo "✅ 服务启动完成!"
echo "📖 API文档: http://localhost:8000/docs"
echo "🔍 健康检查: http://localhost:8000/health"