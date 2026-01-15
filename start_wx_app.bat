@echo off
chcp 65001 >nul
setlocal

REM 获取当前脚本所在目录
set "SCRIPT_DIR=%~dp0"

REM 检查Python环境
python --version >nul 2>&1
if errorlevel 1 (
    echo Python未找到，请确保已安装Python并添加到PATH环境变量
    pause
    exit /b 1
)

REM 安装依赖包
echo 正在安装依赖包...
pip install -r "%SCRIPT_DIR%requirements.txt" --quiet

REM 启动wxPython应用
echo 启动小说创作辅助工具 (wxPython版本)...
cd /d "%~dp0novel_creation_tool"
python run_wx_app.py

pause