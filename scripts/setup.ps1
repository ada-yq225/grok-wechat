# grok-wechat 一键初始化
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Find-Python {
    $candidates = @(
        "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python311\python.exe",
        "$env:LOCALAPPDATA\Programs\Python\Python310\python.exe",
        "$env:USERPROFILE\.local\bin\python3.14.exe",
        "$env:USERPROFILE\.local\bin\python3.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    $cmd = Get-Command python -ErrorAction SilentlyContinue
    if ($cmd -and $cmd.Source -notmatch "WindowsApps") { return $cmd.Source }
    return $null
}

Write-Host "=== grok-wechat 初始化 ===" -ForegroundColor Cyan

$python = Find-Python
if (-not $python) {
    Write-Host "未找到 Python，请先安装 Python 3.10+：https://www.python.org/downloads/" -ForegroundColor Red
    exit 1
}
Write-Host "使用 Python: $python"

if (-not (Test-Path ".venv")) {
    Write-Host "创建虚拟环境..."
    & $python -m venv .venv
}

Write-Host "安装依赖..."
& ".\.venv\Scripts\python.exe" -m pip install --upgrade pip
& ".\.venv\Scripts\pip.exe" install -r requirements.txt

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "已创建 .env，请编辑并填入 XAI_API_KEY" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "下一步：" -ForegroundColor Green
Write-Host "  1. 安装 PC 微信 3.9.x（WeChat.exe），用小号登录"
Write-Host "  2. 编辑 .env，填入 XAI_API_KEY"
Write-Host "  3. 运行环境检查: .\.venv\Scripts\python scripts\check_env.py"
Write-Host "  4. 启动机器人:   .\scripts\start.ps1"