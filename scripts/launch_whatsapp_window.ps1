# 在独立 CMD 窗口启动 WhatsApp 机器人（不会被 IDE 后台任务中断）
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "虚拟环境不存在，请先运行 scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

& ".\.venv\Scripts\python.exe" "scripts\check_whatsapp_env.py"
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

$cmd = "cd /d `"$Root`" && .venv\Scripts\python.exe run_whatsapp.py"
Start-Process -FilePath "cmd.exe" -ArgumentList "/k", $cmd
Write-Host "已在新的 CMD 窗口启动 WhatsApp 机器人。" -ForegroundColor Green
Write-Host "首次登录会自动打开 whatsapp_qr.png，请用手机 WhatsApp 扫描。" -ForegroundColor Yellow