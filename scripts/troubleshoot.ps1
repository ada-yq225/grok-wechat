# WeChatFerry troubleshooting
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent $PSScriptRoot

Write-Host "=== grok-wechat Troubleshoot ===" -ForegroundColor Cyan
Write-Host ""

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
Write-Host ("[Admin] " + $(if ($isAdmin) { "Yes" } else { "No - try run as Administrator" }))

$wechat = Get-Process -Name WeChat -ErrorAction SilentlyContinue
$weixin = Get-Process -Name Weixin -ErrorAction SilentlyContinue
Write-Host ("[WeChat 3.9] " + $(if ($wechat) { "Running PID $($wechat.Id)" } else { "Not running" }))
Write-Host ("[Weixin 4.x] " + $(if ($weixin) { "Running - CLOSE IT, incompatible" } else { "Not running (OK)" }))

Write-Host ""
Write-Host "[Ports 10086/10087]"
netstat -ano | findstr "10086 10087"

$dll = Join-Path $Root ".venv\Lib\site-packages\wcferry\sdk.dll"
Write-Host ""
Write-Host ("[sdk.dll] " + $(if (Test-Path $dll) { "Found" } else { "Missing" }))

Write-Host ""
Write-Host "If WeChatFerry init times out:" -ForegroundColor Yellow
Write-Host "  1. Close Weixin 4.x completely"
Write-Host "  2. Right-click 启动机器人.bat -> Run as administrator"
Write-Host "  3. Add Windows Defender exclusion for:"
Write-Host "     $Root"
Write-Host "  4. Open WeChat 3.9, login, then run login_wechat.py"