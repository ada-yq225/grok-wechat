@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo   Grok 微信机器人 (db_keyboard 模式)
echo ========================================
echo.

echo [1/2] 环境检查...
".venv\Scripts\python.exe" scripts\check_env.py
if errorlevel 1 (
    echo.
    echo 请按上方提示修复后再启动。
    echo 若缺少 WECHAT_DB_KEY，请用 wx_key 提取密钥后写入 .env
    pause
    exit /b 1
)

echo.
echo [2/2] 启动机器人 (Ctrl+C 停止)...
echo 提示: 保持微信窗口打开；发送回复时请勿操作鼠标键盘。
".venv\Scripts\python.exe" run.py
pause