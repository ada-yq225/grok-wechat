"""激活微信窗口后重新探测 UI 树。"""
import time
import win32gui
import win32con
from pywinauto import Desktop

hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
print("hwnd", hwnd)
if hwnd:
    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    win32gui.SetForegroundWindow(hwnd)
    time.sleep(2)

desktop = Desktop(backend="uia")
if hwnd:
    w = desktop.window(handle=hwnd)
    print("class", w.class_name())
    targets = ["会话", "微信", "Chats", "联系人", "搜索"]
    for t in targets:
        try:
            elem = w.child_window(title=t, control_type="Button")
            print(f"Button title={t!r} exists={elem.exists(timeout=0.5)}")
        except Exception as e:
            print(f"Button title={t!r} error={e}")
    for t in ["会话", "Chats", "對話"]:
        try:
            elem = w.child_window(title=t, control_type="List")
            print(f"List title={t!r} exists={elem.exists(timeout=0.5)}")
        except Exception as e:
            print(f"List title={t!r} error={e}")

    render = w.child_window(title="MMUIRenderSubWindowHW", control_type="Pane")
    print("MMUIRender exists", render.exists(timeout=0.5))
    if render.exists(timeout=0.1):
        kids = render.children()
        print("MMUIRender children", len(kids))
        for c in kids[:20]:
            print(" ", c.element_info.control_type, c.class_name(), repr(c.window_text()[:40]))