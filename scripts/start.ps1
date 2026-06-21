# Start grok-wechat bot
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Get-EnvValue {
    param([string]$Key, [string]$Default = "")
    if (-not (Test-Path ".\.env")) { return $Default }
    foreach ($line in Get-Content ".\.env" -Encoding UTF8) {
        $trimmed = $line.Trim()
        if ($trimmed.StartsWith("#") -or -not $trimmed.Contains("=")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts[0].Trim() -eq $Key) { return $parts[1].Trim() }
    }
    return $Default
}

function Test-WeixinRunning {
    return [bool](Get-Process -Name Weixin -ErrorAction SilentlyContinue)
}

function Test-WeChatRunning {
    return [bool](Get-Process -Name WeChat -ErrorAction SilentlyContinue)
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Virtual env missing. Run: .\scripts\setup.ps1" -ForegroundColor Red
    exit 1
}

$Backend = (Get-EnvValue "WECHAT_BACKEND" "db_keyboard").ToLower()

Write-Host "Environment check..."
& ".\.venv\Scripts\python.exe" "scripts\check_env.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "Fix the issues above before starting." -ForegroundColor Red
    exit $LASTEXITCODE
}

if ($Backend -eq "db_keyboard" -or $Backend -eq "pyweixin") {
    if (-not (Test-WeixinRunning)) {
        $WeixinExe = "C:\Program Files\Tencent\Weixin\Weixin.exe"
        if (Test-Path $WeixinExe) {
            Write-Host ""
            Write-Host "Launching Weixin 4.x..." -ForegroundColor Yellow
            Start-Process $WeixinExe
            Start-Sleep -Seconds 3
        }
    }

    if (-not (Test-WeixinRunning)) {
        Write-Host "Weixin 4.x is not running. Open it and log in first." -ForegroundColor Red
        exit 1
    }

    Write-Host ""
    Write-Host "IMPORTANT: Keep Weixin open while the bot runs." -ForegroundColor Yellow
    if ($Backend -eq "db_keyboard") {
        Write-Host "Do not use mouse/keyboard while the bot is sending replies." -ForegroundColor Yellow
    }
    Write-Host "Send a private message to your bot account to chat with Grok." -ForegroundColor Yellow
} else {
    $WeChatExe = "C:\Program Files\Tencent\WeChat\WeChat.exe"
    if (-not (Test-WeChatRunning)) {
        if (-not (Test-Path $WeChatExe)) {
            Write-Host "PC WeChat 3.9 not found. Run: .\scripts\install_wechat39.ps1" -ForegroundColor Red
            exit 1
        }
        Write-Host ""
        Write-Host "Launching PC WeChat 3.9..." -ForegroundColor Yellow
        Start-Process $WeChatExe
        Start-Sleep -Seconds 3
    }

    if (-not (Test-WeChatRunning)) {
        Write-Host "WeChat failed to start. Open it manually:" -ForegroundColor Red
        Write-Host "  $WeChatExe"
        exit 1
    }

    Write-Host ""
    Write-Host "IMPORTANT: Log in with your bot WeChat account (WeChat 3.9)." -ForegroundColor Yellow
    Write-Host "Press Enter after login is complete..."
    Read-Host
}

Write-Host ""
Write-Host "Starting Grok WeChat bot (Ctrl+C to stop)..." -ForegroundColor Cyan
& ".\.venv\Scripts\python.exe" "run.py"