# 讲述人预热 + 引导重新登录微信
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$Python = Join-Path $Root ".venv\Scripts\python.exe"
$Minutes = 5

function Test-WeixinRunning {
    return [bool](Get-Process -Name Weixin -ErrorAction SilentlyContinue)
}

function Ensure-Narrator {
    if (Get-Process -Name Narrator -ErrorAction SilentlyContinue) {
        Write-Host "[OK] 讲述人已在运行" -ForegroundColor Green
        return
    }
    Write-Host "正在启动讲述人 (Win+Ctrl+Enter 可开关)..." -ForegroundColor Yellow
    Start-Process "Narrator.exe"
    Start-Sleep -Seconds 2
    if (-not (Get-Process -Name Narrator -ErrorAction SilentlyContinue)) {
        throw "讲述人启动失败，请手动按 Win+Ctrl+Enter"
    }
    Write-Host "[OK] 讲述人已启动" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== 微信无障碍预热 ===" -ForegroundColor Cyan
Write-Host ""

if (Test-WeixinRunning) {
    Write-Host "[!!] 检测到微信正在运行，请先完全退出微信后再运行本脚本。" -ForegroundColor Red
    Write-Host "     托盘图标 -> 退出" -ForegroundColor Yellow
    exit 1
}

Ensure-Narrator

Write-Host ""
Write-Host "讲述人需保持运行 $Minutes 分钟，期间不要登录微信。" -ForegroundColor Yellow
Write-Host "可以静音讲述人，但不要关闭。" -ForegroundColor Gray
Write-Host ""

for ($i = $Minutes; $i -ge 1; $i--) {
    for ($s = 59; $s -ge 0; $s--) {
        Write-Host ("`r等待中... {0:D2}:{1:D2}  讲述人请保持开启" -f $i, $s) -NoNewline
        Start-Sleep -Seconds 1
    }
}
Write-Host ""
Write-Host ""
Write-Host "[OK] 预热完成。现在请：" -ForegroundColor Green
Write-Host "  1. 打开微信并登录小号"
Write-Host "  2. 登录后运行: .\.venv\Scripts\python scripts\check_weixin_ui.py"
Write-Host "  3. 显示 [OK] 后，再运行: .\.venv\Scripts\python run.py"
Write-Host ""
Write-Host "讲述人现在可以关闭 (Win+Ctrl+Enter)。" -ForegroundColor Gray
Read-Host "登录完成后按 Enter 检查 UI"

& $Python "$PSScriptRoot\check_weixin_ui.py"
exit $LASTEXITCODE