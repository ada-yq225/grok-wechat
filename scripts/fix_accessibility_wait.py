"""讲述人预热：退出微信并等待指定分钟数后检查 UI。"""
from __future__ import annotations

import subprocess
import sys
import time
from datetime import datetime, timedelta

WAIT_MINUTES = 10


def narrator_running() -> bool:
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Process -Name Narrator -ErrorAction SilentlyContinue | Measure-Object).Count",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return (r.stdout or "").strip() not in {"", "0"}


def weixin_running() -> bool:
    r = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Process -Name Weixin -ErrorAction SilentlyContinue | Measure-Object).Count",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return int((r.stdout or "0").strip()) > 0
    except ValueError:
        return False


def stop_weixin() -> None:
    subprocess.run(
        ["taskkill", "/IM", "Weixin.exe", "/F"],
        capture_output=True,
        check=False,
    )


def start_narrator() -> None:
    subprocess.run(["powershell", "-NoProfile", "-Command", "Start-Process Narrator.exe"], check=False)
    time.sleep(2)


def main() -> int:
    print("=== 修复：讲述人预热 ===")
    print(f"目标：讲述人连续运行 {WAIT_MINUTES} 分钟，期间微信保持关闭\n")

    if weixin_running():
        print("[1/4] 正在退出微信进程...")
        stop_weixin()
        time.sleep(3)
        if weixin_running():
            print("  [X] 微信仍在运行，请手动托盘退出后重试")
            return 1
        print("  [OK] 微信已退出")
    else:
        print("[1/4] 微信未运行 [OK]")

    print("[2/4] 启动讲述人...")
    if not narrator_running():
        start_narrator()
    if not narrator_running():
        print("  [X] 讲述人启动失败，请按 Win+Ctrl+Enter")
        return 1
    print("  [OK] 讲述人运行中")

    deadline = datetime.now() + timedelta(minutes=WAIT_MINUTES)
    print(f"[3/4] 等待 {WAIT_MINUTES} 分钟（截止 {deadline.strftime('%H:%M:%S')}）...")
    print("      期间请勿打开微信\n")
    while datetime.now() < deadline:
        left = int((deadline - datetime.now()).total_seconds())
        mins, secs = divmod(left, 60)
        print(f"\r  剩余 {mins:02d}:{secs:02d}  ", end="", flush=True)
        time.sleep(1)
    print("\n  [OK] 预热完成")

    print("[4/4] 现在请打开微信并登录小号，登录后按 Enter...")
    try:
        input()
    except EOFError:
        print("（非交互模式，跳过等待登录）")

    root = __file__.replace("\\", "/").rsplit("/", 1)[0]
    check = subprocess.run(
        [sys.executable, f"{root}/check_weixin_ui.py"],
        check=False,
    )
    test = subprocess.run(
        [sys.executable, f"{root}/test_open_weixin.py"],
        check=False,
    )
    return 0 if check.returncode == 0 and test.returncode == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())