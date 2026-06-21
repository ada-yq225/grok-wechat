# Add Windows Defender exclusion for grok-wechat (requires Administrator)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot

$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "Re-launching as Administrator..."
    Start-Process powershell -Verb RunAs -ArgumentList "-ExecutionPolicy Bypass -File `"$PSCommandPath`""
    exit
}

Write-Host "Adding Defender exclusion: $Root"
Add-MpPreference -ExclusionPath $Root
Write-Host "Done. You can now run 启动机器人.bat"
Read-Host "Press Enter to close"