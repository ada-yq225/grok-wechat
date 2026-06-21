import subprocess
from datetime import datetime

ps = """
$n = Get-Process -Name Narrator -ErrorAction SilentlyContinue | Select-Object -First 1
$w = Get-Process -Name Weixin -ErrorAction SilentlyContinue |
  Where-Object { $_.CommandLine -notmatch '--type=' -or $_.MainWindowTitle -ne '' } |
  Select-Object -First 1
if (-not $w) {
  $w = Get-Process -Name Weixin -ErrorAction SilentlyContinue |
    Sort-Object StartTime | Select-Object -First 1
}
[PSCustomObject]@{
  NarratorStart = if ($n) { $n.StartTime.ToString('yyyy-MM-dd HH:mm:ss') } else { 'none' }
  WeixinStart   = if ($w) { $w.StartTime.ToString('yyyy-MM-dd HH:mm:ss') } else { 'none' }
  WeixinPid     = if ($w) { $w.Id } else { 0 }
} | Format-List
"""
print(subprocess.run(["powershell","-NoProfile","-Command",ps],capture_output=True,text=True).stdout)