"""通过 WeChatFerry 辅助登录 PC 微信 3.9。"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WECHAT_EXE = Path(r"C:\Program Files\Tencent\WeChat\WeChat.exe")
QR_FILE = ROOT / "login_qrcode.png"
INIT_TIMEOUT = 45
LOGIN_TIMEOUT = 120


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


def ensure_wechat_running() -> None:
    if wechat_running():
        print("[OK] PC 微信已在运行")
        return
    if not WECHAT_EXE.exists():
        print(f"[失败] 未找到 {WECHAT_EXE}")
        print("请先运行 scripts\\install_wechat39.ps1")
        raise SystemExit(1)
    print("[..] 正在启动 PC 微信 3.9...")
    subprocess.Popen([str(WECHAT_EXE)], shell=False)
    for _ in range(15):
        time.sleep(1)
        if wechat_running():
            print("[OK] PC 微信已启动")
            return
    print("[失败] 微信未能启动，请手动打开 WeChat.exe")
    raise SystemExit(1)


def connect_wcf():
    import threading

    from wcferry import Wcf

    holder: dict = {}

    def _init() -> None:
        try:
            holder["wcf"] = Wcf(debug=True, block=False)
        except Exception as exc:
            holder["error"] = exc

    thread = threading.Thread(target=_init, daemon=True)
    thread.start()
    thread.join(INIT_TIMEOUT)
    if thread.is_alive():
        print(f"[失败] WeChatFerry 初始化超时（{INIT_TIMEOUT} 秒）")
        print("这通常表示 DLL 注入失败。请确认：")
        print("  1. 已用管理员身份运行（启动机器人.bat 会自动请求）")
        print("  2. Windows Defender 已排除本项目文件夹")
        print("  3. 已关闭 Weixin 4.x")
        print(r"  4. 运行: .\scripts\troubleshoot.ps1")
        raise SystemExit(1)
    if "error" in holder:
        print(f"[失败] WeChatFerry 初始化异常: {holder['error']}")
        raise SystemExit(1)
    wcf = holder.get("wcf")
    if wcf is None:
        print("[失败] WeChatFerry 未返回连接")
        raise SystemExit(1)
    return wcf


def save_qrcode(qr_data: str) -> None:
    if not qr_data:
        return
    path = Path(qr_data)
    if path.exists():
        target = QR_FILE
        if path.resolve() != target.resolve():
            target.write_bytes(path.read_bytes())
        os.startfile(target)
        print(f"[..] 已打开登录二维码: {target}")
        return
    if qr_data.startswith("data:image") or len(qr_data) > 200:
        import base64

        payload = qr_data.split(",", 1)[-1]
        QR_FILE.write_bytes(base64.b64decode(payload))
        os.startfile(QR_FILE)
        print(f"[..] 已打开登录二维码: {QR_FILE}")
        return
    print(f"[..] 二维码数据: {qr_data[:120]}...")


def main() -> int:
    print("=== PC 微信登录助手 ===\n")
    ensure_wechat_running()
    print("[..] 连接 WeChatFerry...")
    wcf = connect_wcf()

    if wcf.is_login():
        user = wcf.get_user_info()
        print(f"[成功] 已登录: {user.get('name', '')} ({wcf.get_self_wxid()})")
        return 0

    print("[..] 微信未登录，获取二维码...")
    try:
        qr = wcf.get_qrcode()
        save_qrcode(qr)
    except Exception as exc:
        print(f"[提示] 无法自动获取二维码: {exc}")
        print("请在 PC 微信窗口中手动扫码登录。")

    print(f"[..] 等待扫码登录（最多 {LOGIN_TIMEOUT} 秒）...")
    deadline = time.monotonic() + LOGIN_TIMEOUT
    while time.monotonic() < deadline:
        if wcf.is_login():
            user = wcf.get_user_info()
            print(f"[成功] 已登录: {user.get('name', '')} ({wcf.get_self_wxid()})")
            print("现在可以启动机器人: .\\scripts\\start.ps1")
            return 0
        time.sleep(2)

    print("[失败] 超时未登录。请确认已用手机微信扫码。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())