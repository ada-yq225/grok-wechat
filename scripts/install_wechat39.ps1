# Install PC WeChat 3.9.12.51 for WeChatFerry compatibility
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
$TargetDir = Join-Path $Root "wechat39"
$Installer = Join-Path $env:TEMP "WeChatSetup-3.9.12.51.exe"
$DownloadUrl = "https://github.com/tom-snow/wechat-windows-versions/releases/download/v3.9.12.51/WeChatSetup-3.9.12.51.exe"

Write-Host "=== Install PC WeChat 3.9.12.51 ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Weixin 4.x is NOT compatible with WeChatFerry."
Write-Host "Install WeChat 3.9.x to: $TargetDir"
Write-Host "Then log in with your bot WeChat account."
Write-Host ""

if (Test-Path (Join-Path $TargetDir "WeChat.exe")) {
    Write-Host "Found $TargetDir\WeChat.exe - skip install." -ForegroundColor Green
    exit 0
}

Write-Host "Downloading installer..."
try {
    Invoke-WebRequest -Uri $DownloadUrl -OutFile $Installer -UseBasicParsing
}
catch {
    Write-Host "Download failed. Get it manually:" -ForegroundColor Yellow
    Write-Host "https://github.com/tom-snow/wechat-windows-versions/releases/tag/v3.9.12.51"
    exit 1
}

New-Item -ItemType Directory -Force -Path $TargetDir | Out-Null
Write-Host "Run installer and set install path to:" -ForegroundColor Yellow
Write-Host $TargetDir
Start-Process -FilePath $Installer -Wait