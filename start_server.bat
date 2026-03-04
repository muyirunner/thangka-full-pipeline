@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion
set "ROOT_DIR=%CD%"

title Time Restoration Lab - Startup

echo.
echo ===============================================================================
echo                时空修复实验室 (Time Restoration Lab) 
echo                            一键启动脚本
echo ===============================================================================
echo.

:: 1. 启动统一后端 (FastAPI)
echo [1/2] 正在启动统一算法集群 (Tashi's Brain)...
powershell -NoProfile -Command "Start-Process cmd.exe -WindowStyle Normal -ArgumentList '/k', 'python app.py' -WorkingDirectory '%ROOT_DIR%\backend'" >nul 2>&1
echo OK: Backend AI Service starting on port 8000

:: 2. 启动全新游戏前端 (Vite Vue3)
echo [2/2] 正在构建数字实验室前端 (Tashi's UI)...
powershell -NoProfile -Command "Start-Process cmd.exe -WindowStyle Normal -ArgumentList '/k', 'npm run dev' -WorkingDirectory '%ROOT_DIR%\frontend'" >nul 2>&1
echo OK: Frontend Service starting on port 5173

echo.
echo ===============================================================================
echo                            实验室已激活！
echo ===============================================================================
echo.
echo Please wait 10 seconds for Tashi to wake up...
pause >nul

:: Open browser
powershell -NoProfile -Command "Start-Process http://localhost:5173" >nul 2>&1

echo.
echo 已在浏览器中唤醒 Tashi。请保持此窗口开启。
echo.
pause
goto :eof
