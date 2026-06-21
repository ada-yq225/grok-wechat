import subprocess
import sys
import time
from datetime import datetime, timedelta

WAIT_MINUTES = 10
deadline = datetime.now() + timedelta(minutes=WAIT_MINUTES)
print(f"讲述人预热中，请勿打开微信。截止 {deadline.strftime('%H:%M:%S')}")
while datetime.now() < deadline:
    left = int((deadline - datetime.now()).total_seconds())
    m, s = divmod(left, 60)
    print(f"\r剩余 {m:02d}:{s:02d}", end="", flush=True)
    time.sleep(1)
print("\n预热完成。现在可以打开微信登录。")
r = subprocess.run(
    ["powershell", "-NoProfile", "-Command",
     "(Get-Process -Name Weixin -ErrorAction SilentlyContinue | Measure-Object).Count"],
    capture_output=True, text=True,
)
if (r.stdout or "").strip() not in {"", "0"}:
    print("检测到微信已运行，开始检查 UI...")
    sys.exit(subprocess.call([sys.executable, __file__.replace("wait_narrator.py", "check_weixin_ui.py")]))
print("请登录微信后运行: python scripts/check_weixin_ui.py")