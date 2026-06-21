"""全面诊断 pyweixin 运行环境。"""

from __future__ import annotations

import platform
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import psutil
import win32gui
from pywinauto import Desktop

ROOT = Path(__file__).resolve().parents[1]


def section(title: str) -> None:
    print(f"\n{'=' * 50}")
    print(title)
    print('=' * 50)


def run_ps(script: str) -> str:
    result = subprocess.run(
        ["powershell", "-NoProfile", "-Command", script],
        capture_output=True,
        text=True,
        check=False,
    )
    return (result.stdout or result.stderr).strip()


def enum_weixin_windows() -> list[tuple[int, str, str]]:
    rows: list[tuple[int, str, str]] = []

    def callback(hwnd, _):
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        if title in ("微信", "Weixin") or "weixin" in cls.lower() or "mmui" in cls.lower():
            rows.append((hwnd, cls, title))

    win32gui.EnumWindows(callback, None)
    return rows


def count_mmui(window, depth: int = 0, limit: int = 500) -> tuple[int, list[str]]:
    found: list[str] = []
    count = 0

    def walk(elem, d: int = 0) -> None:
        nonlocal count
        if d > 10 or count >= limit:
            return
        try:
            cls = elem.class_name()
            if "mmui" in cls or "MMUI" in cls:
                count += 1
                if len(found) < 15:
                    found.append(f"{'  ' * d}{cls} | {elem.window_text()[:30]!r}")
            for child in elem.children():
                walk(child, d + 1)
        except Exception:
            return

    walk(window)
    return count, found


def main() -> int:
    print("grok-wechat 全面诊断")
    print("时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    section("1. 系统与 Python")
    print("OS:", platform.system(), platform.release(), platform.version())
    print("Python:", sys.version.split()[0])
    print("项目:", ROOT)

    section("2. 讲述人 / 无障碍服务")
    narrator_count = run_ps(
        "(Get-Process -Name Narrator -ErrorAction SilentlyContinue | Measure-Object).Count"
    )
    print("Narrator 进程数:", narrator_count)
    if narrator_count == "0":
        print("  [!] 讲述人未运行")
    else:
        info = run_ps(
            "Get-Process -Name Narrator -ErrorAction SilentlyContinue | "
            "Select-Object Id,StartTime | Format-List | Out-String -Width 200"
        )
        print(info)

    section("3. 显示缩放")
    dpi = run_ps(
        "Add-Type -AssemblyName System.Windows.Forms; "
        "[System.Windows.Forms.SystemInformation]::DpiX"
    )
    try:
        scale = int(float(dpi)) / 96 * 100
        print(f"DPI={dpi}  缩放约 {scale:.0f}%")
        if scale != 100:
            print("  [!] 非 100% 缩放可能影响 UI 自动化 (issue #147)")
    except Exception:
        print("DPI 读取失败:", dpi)

    section("4. 微信进程")
    weixin_procs = []
    for proc in psutil.process_iter(["pid", "name", "create_time", "cmdline"]):
        name = (proc.info.get("name") or "").lower()
        if name in ("weixin.exe", "wechat.exe"):
            cmd = " ".join(proc.info.get("cmdline") or [])
            weixin_procs.append((proc.info["pid"], name, cmd[:120]))
    if not weixin_procs:
        print("  [X] 无微信进程")
    else:
        for pid, name, cmd in weixin_procs:
            print(f"  PID={pid} {name}")
            print(f"    cmd={cmd}")

    section("5. pyweixin 基础信息")
    try:
        from pyweixin.WeChatTools import Tools

        print("is_weixin_running:", Tools.is_weixin_running())
        info = Tools.about_weixin()
        for k, v in info.items():
            print(f"  {k}: {v}")
    except Exception as exc:
        print("  [X] pyweixin 错误:", exc)

    section("6. 微信窗口枚举")
    desktop = Desktop(backend="uia")
    windows = enum_weixin_windows()
    if not windows:
        print("  [X] 未找到标题为 微信/Weixin 的窗口")
    for hwnd, cls, title in windows:
        print(f"\n  hwnd=0x{hwnd:X} win32_class={cls!r} title={title!r}")
        try:
            w = desktop.window(handle=hwnd)
            uia_cls = w.class_name()
            rect = w.rectangle()
            visible = w.is_visible()
            enabled = w.is_enabled()
            print(f"    uia_class={uia_cls!r} visible={visible} enabled={enabled}")
            print(f"    rect=({rect.left},{rect.top},{rect.right},{rect.bottom})")
            mmui_count, samples = count_mmui(w)
            print(f"    mmui节点数={mmui_count}")
            for line in samples:
                print(f"      {line}")
            children = w.children()
            print(f"    直接子节点={len(children)}")
            for child in children[:8]:
                print(
                    f"      - {child.element_info.control_type} "
                    f"{child.class_name()!r} {child.window_text()[:40]!r}"
                )
        except Exception as exc:
            print(f"    [X] 读取失败: {exc}")

    section("7. open_weixin 实测")
    try:
        from pyweixin.WeChatTools import Navigator

        win = Navigator.open_weixin(is_maximize=False)
        print("  [OK] open_weixin 成功, class=", win.class_name())
    except Exception as exc:
        print(f"  [X] open_weixin 失败: {type(exc).__name__}: {exc}")

    section("8. 结论")
    main_ok = False
    for hwnd, _, title in windows:
        if title == "微信":
            try:
                w = desktop.window(handle=hwnd)
                if w.class_name() == "mmui::MainWindow" or count_mmui(w)[0] > 0:
                    main_ok = True
            except Exception:
                pass
    if main_ok:
        print("  微信 UI 无障碍已就绪，可以运行 run.py")
        return 0
    print("  微信 UI 未就绪。常见原因：")
    print("    A. 讲述人未在微信登录前运行够久 (建议 10 分钟)")
    print("    B. 该账号被微信限制 UIAutomation (可尝试切换账号)")
    print("    C. 微信版本 4.1.10.53 讲述人无效 (GitHub issue #251/#270)")
    print("    D. 显示缩放非 100%")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())