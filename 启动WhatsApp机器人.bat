@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo.
echo ========================================
echo   Grok WhatsApp 机器人 (后台模式)
echo ========================================
echo.

echo [1/2] 环境检查...
".venv\Scripts\python.exe" scripts\check_whatsapp_env.py
if errorlevel 1 (
    echo.
    echo 请按上方提示修复后再启动。
    pause
    exit /b 1
)

echo.
echo [2/2] 启动机器人（独立窗口，关闭窗口即停止）...
echo 首次运行会自动打开 whatsapp_qr.png，用手机 WhatsApp 扫描
start "Grok WhatsApp" cmd /k "cd /d %~dp0 && .venv\Scripts\python.exe run_whatsapp.py"
echo 已在新窗口启动。请勿关闭标题为 Grok WhatsApp 的黑色窗口。
pause