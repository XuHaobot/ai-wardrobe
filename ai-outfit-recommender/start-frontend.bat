@echo off
chcp 65001 > nul
echo ====================
echo  AI衣橱前端 - 启动脚本
echo ====================
echo.

REM 检查 node_modules 是否存在
if not exist "node_modules\" (
    echo [1/2] 首次运行，正在安装依赖（可能需要几分钟）...
    call npm install
    if errorlevel 1 (
        echo [错误] 依赖安装失败！
        pause
        exit /b 1
    )
) else (
    echo [1/2] 依赖已存在，跳过安装
)

echo.
echo [2/2] 启动前端开发服务器...
echo 启动后访问: http://localhost:5173
echo 按 Ctrl+C 停止服务
echo ====================
echo.
call npm run dev
