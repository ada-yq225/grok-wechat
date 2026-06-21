"""快速测试 WeChatFerry 能否连接已登录的 PC 微信 3.9。"""

from __future__ import annotations

import subprocess
import sys
import time

LOGIN_TIMEOUT_SEC = 60


def wechat_running() -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Process -Name WeChat -ErrorAction SilentlyContinue | "
            "Measure-Object).Count -gt 0",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip().lower() == "true"


def main() -> int:
    print("=== WeChatFerry 连接测试 ===\n")

    if not wechat_running():
        print("[失败] PC 微信 3.9 未运行。")
        print("请先手动打开并登录：")
        print(r'  "C:\Program Files\Tencent\WeChat\WeChat.exe"')
        print("注意：必须用 WeChat.exe（3.9），不是 Weixin 4.x。")
        return 1

    print("[OK] 检测到 WeChat.exe 进程")
    print(f"正在连接 WeChatFerry（最多等待 {LOGIN_TIMEOUT_SEC} 秒）...\n")

    try:
        from wcferry import Wcf
    except ImportError:
        print("[失败] 未安装 wcferry，请运行 scripts\\setup.ps1")
        return 1

    try:
        wcf = Wcf(debug=True, block=False)
    except Exception as exc:
        print(f"[失败] 连接异常: {exc}")
        return 1

    deadline = time.monotonic() + LOGIN_TIMEOUT_SEC
    while time.monotonic() < deadline:
        if wcf.is_login():
            user = wcf.get_user_info()
            wxid = wcf.get_self_wxid()
            print(f"[成功] 已登录: {user.get('name', '')} ({wxid})")
            print("可以启动机器人: .\\scripts\\start.ps1")
            return 0
        time.sleep(1)

    print(f"[失败] {LOGIN_TIMEOUT_SEC} 秒内微信未完成登录。")
    print("请在 PC 微信窗口中用小号扫码登录，然后重新运行本脚本。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())