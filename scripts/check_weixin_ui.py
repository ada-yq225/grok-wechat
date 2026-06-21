"""检查微信主窗口 UI 是否可被 pyweixin 识别。"""

from __future__ import annotations

import subprocess
import sys

import win32gui
from pywinauto import Desktop


def _narrator_running() -> bool:
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-Command",
            "(Get-Process -Name Narrator -ErrorAction SilentlyContinue | "
            "Measure-Object).Count",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        return int(result.stdout.strip() or "0") > 0
    except ValueError:
        return False


def _count_mmui_nodes(window) -> int:
    count = 0

    def walk(elem, depth: int = 0) -> None:
        nonlocal count
        if depth > 8:
            return
        try:
            if "mmui" in elem.class_name():
                count += 1
            for child in elem.children():
                walk(child, depth + 1)
        except Exception:
            return

    walk(window)
    return count


def _count_real_mmui(window) -> int:
    """排除 MMUIRenderSubWindowHW 空壳节点。"""
    count = 0

    def walk(elem, depth: int = 0) -> None:
        nonlocal count
        if depth > 12:
            return
        try:
            cls = elem.class_name()
            if cls.startswith("mmui::") and cls != "MMUIRenderSubWindowHW":
                count += 1
            for child in elem.children():
                walk(child, depth + 1)
        except Exception:
            return

    walk(window)
    return count


def main() -> int:
    hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
    if hwnd == 0:
        hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "Weixin")
    if hwnd == 0:
        print("  [XX] 未找到微信窗口，请先打开并登录微信")
        return 1

    window = Desktop(backend="uia").window(handle=hwnd)
    class_name = window.class_name()
    mmui_count = _count_mmui_nodes(window)
    real_mmui = _count_real_mmui(window)
    if class_name == "mmui::MainWindow" or real_mmui > 0:
        print(
            f"  [OK] 微信 UI 可识别 (class={class_name}, mmui控件={real_mmui})"
        )
        return 0

    print(f"  [XX] 微信 UI 不可识别 (class={class_name}, mmui节点={mmui_count})")
    if _narrator_running():
        print("  [!!] 讲述人已在运行，但微信仍未暴露 UI（4.1.10 上较常见）")
        print("  [!!] 请尝试：")
        print("       1. 重启电脑")
        print("       2. 开机后先开讲述人，等待 10 分钟（期间不要开微信）")
        print("       3. 再登录微信；或先登录另一个微信号，再切回小号")
        print("       4. 将系统显示缩放调到 100% 后重试")
    else:
        print("  [!!] 需先运行讲述人 5-10 分钟，再重新登录微信")
        print("  [!!] 运行: .\\scripts\\prepare_weixin_login.ps1")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())