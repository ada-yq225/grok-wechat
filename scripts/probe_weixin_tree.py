import win32gui
from pywinauto import Desktop


def enum_callback(hwnd, results):
    title = win32gui.GetWindowText(hwnd)
    if title in ("微信", "Weixin"):
        results.append(hwnd)


handles: list[int] = []
win32gui.EnumWindows(enum_callback, handles)

desktop = Desktop(backend="uia")


def walk(elem, depth=0, limit=80):
    if depth > 12 or limit <= 0:
        return limit
    try:
        cls = elem.class_name()
        text = (elem.window_text() or "")[:50]
        ctype = elem.element_info.control_type
        if cls or text or "mmui" in cls.lower() or "MMUI" in cls:
            print("  " * depth + f"{ctype} {cls!r} {text!r}")
        for child in elem.children():
            limit = walk(child, depth + 1, limit)
            if limit <= 0:
                break
    except Exception as exc:
        print("  " * depth + f"<error {exc}>")
    return limit - 1


for hwnd in handles:
    print(f"\n=== hwnd={hwnd} title={win32gui.GetWindowText(hwnd)!r} ===")
    w = desktop.window(handle=hwnd)
    walk(w)