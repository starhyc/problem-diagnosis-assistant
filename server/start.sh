#!/bin/bash

echo "========================================"
echo "AIOps 智能诊断平台 - 后端服务启动"
echo "========================================"
echo ""

# 检查 Python 是否安装
if ! command -v python3 &> /dev/null; then
    echo "[错误] 未检测到 Python3，请先安装 Python 3.8+"
    exit 1
fi

echo "[1/4] 检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "[信息] 创建虚拟环境..."
    python3 -m venv venv
fi

echo "[2/4] 激活虚拟环境..."
source venv/bin/activate

echo "[3/4] 安装依赖..."
pip install -r requirements.txt -q

echo "[4/4] 初始化数据库..."
python init_db.py

echo ""
echo "========================================"
echo "启动 FastAPI 服务器..."
echo "========================================"
echo ""
echo "API 文档: http://localhost:8000/docs"
echo "按 Ctrl+C 停止服务器"
echo ""

uvicorn main:app --reload --host 0.0.0.0 --port 8000
