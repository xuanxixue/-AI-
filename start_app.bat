@echo off
chcp 65001 > nul
setlocal

REM 设置Python路径
set PYTHON_CMD=python

REM 检查Python是否可用
%PYTHON_CMD% --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到Python命令，请确保已安装Python并添加到PATH环境变量中。
    pause
    exit /b 1
)

echo 启动小说创作辅助工具...
echo.

REM 运行应用
cd /d "%~dp0novel_creation_tool"
%PYTHON_CMD% main.py

pause