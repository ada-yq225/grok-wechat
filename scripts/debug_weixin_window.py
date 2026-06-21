import win32gui
from pywinauto import Desktop


def callback(hwnd, results):
    title = win32gui.GetWindowText(hwnd)
    cls = win32gui.GetClassName(hwnd)
    if title in ("微信", "Weixin") or cls.startswith("mmui") or "Weixin" in cls:
        results.append((hwnd, cls, title))


results: list[tuple[int, str, str]] = []
win32gui.EnumWindows(callback, results)

print("=== 微信相关窗口 ===")
for hwnd, cls, title in results:
    print(f"hwnd={hwnd} class={cls!r} title={title!r}")
    try:
        w = Desktop(backend="uia").window(handle=hwnd)
        print(f"  uia.class_name={w.class_name()!r}")
    except Exception as exc:
        print(f"  uia error: {exc}")

narrator = __import__("subprocess").run(
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
print(f"\n讲述人进程数: {narrator.stdout.strip()}")