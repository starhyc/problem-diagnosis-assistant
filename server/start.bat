@echo off
echo ========================================
echo AIOps 智能诊断平台 - 后端服务启动
echo ========================================
echo.

REM 检查 Python 是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo [1/4] 检查虚拟环境...
if not exist "venv" (
    echo [信息] 创建虚拟环境...
    python -m venv venv
)

echo [2/4] 激活虚拟环境...
call venv\Scripts\activate.bat

echo [3/4] 安装依赖...
pip install -r requirements.txt -q

echo [4/4] 初始化数据库...
python init_db.py

echo.
echo ========================================
echo 启动 FastAPI 服务器...
echo ========================================
echo.
echo API 文档: http://localhost:8000/docs
echo 按 Ctrl+C 停止服务器
echo.

uvicorn main:app --reload --host 0.0.0.0 --port 8000
