@echo off
chcp 65001
echo ================================
echo 开始执行批量截图脚本...
echo ================================

REM 检查 Python 是否安装
python --version >nul 2>&1
if errorlevel 1 (
    echo 未检测到 Python，请先安装 Python 并配置环境变量。
    pause
    exit /b 1
)

REM 安装依赖（可选，确保依赖都安装）
echo 正在检查并安装依赖库...
pip install --quiet --upgrade pandas openpyxl tqdm playwright

REM 确认 Playwright 浏览器依赖是否安装
echo 正在确认 Playwright 浏览器驱动...
playwright --version >nul 2>&1
if errorlevel 1 (
    echo 正在安装 Playwright 浏览器依赖，请稍候...
    playwright install
)

REM 运行 Python 脚本
echo 正在运行 Python 脚本...
python screenshot_domains.py

echo ================================
echo 脚本执行完毕，按任意键退出。
pause >nul
