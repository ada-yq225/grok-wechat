# 为 pyweixin 启用微信 UI 无障碍（讲述人）
# 官方说明：讲述人需在微信登录前运行 5 分钟以上
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== 微信 UI 无障碍设置 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "pyweixin 需要 Windows 讲述人先运行，微信才能暴露 UI 结构。" -ForegroundColor Yellow
Write-Host "若你已登录微信但机器人报错，请按以下步骤操作：" -ForegroundColor Yellow
Write-Host ""
Write-Host "  1. 完全退出微信（托盘图标 -> 退出）"
Write-Host "  2. 运行本脚本启动讲述人"
Write-Host "  3. 保持讲述人运行至少 5 分钟（可静音）"
Write-Host "  4. 打开微信并重新登录小号"
Write-Host "  5. 讲述人可关闭，再启动机器人"
Write-Host ""

$narrator = Get-Process -Name "Narrator" -ErrorAction SilentlyContinue
if ($narrator) {
    Write-Host "[OK] 讲述人已在运行 (PID $($narrator.Id))" -ForegroundColor Green
} else {
    Write-Host "正在启动讲述人..." -ForegroundColor Yellow
    Start-Process "Narrator.exe"
    Start-Sleep -Seconds 2
    $narrator = Get-Process -Name "Narrator" -ErrorAction SilentlyContinue
    if ($narrator) {
        Write-Host "[OK] 讲述人已启动" -ForegroundColor Green
        Write-Host "提示: Win+Ctrl+Enter 可开关讲述人；可在设置里调低音量。" -ForegroundColor Gray
    } else {
        Write-Host "[!!] 讲述人启动失败，请手动按 Win+Ctrl+Enter 开启" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "检查微信 UI 是否可识别..."
& "$PSScriptRoot\..\.venv\Scripts\python.exe" "$PSScriptRoot\check_weixin_ui.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "UI 尚不可识别。若微信已登录，请先退出微信，讲述人运行 5 分钟后再重新登录。" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "微信 UI 已就绪，可以启动机器人。" -ForegroundColor Green
exit 0