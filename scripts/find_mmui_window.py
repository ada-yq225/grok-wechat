import win32gui
import win32process
import psutil
from pywinauto import Desktop

desktop = Desktop(backend="uia")
found = []

def callback(hwnd, _):
    try:
        if not win32gui.IsWindowVisible(hwnd):
            return
        title = win32gui.GetWindowText(hwnd)
        cls = win32gui.GetClassName(hwnd)
        _, pid = win32process.GetWindowThreadProcessId(hwnd)
        try:
            pname = psutil.Process(pid).name()
        except Exception:
            pname = "?"
        if "mmui" in cls or (pname.lower() == "weixin.exe" and title):
            w = desktop.window(handle=hwnd)
            uia = w.class_name()
            if "mmui" in uia or uia == "mmui::MainWindow":
                found.append((hwnd, title, cls, uia, pname, pid))
    except Exception:
        pass

win32gui.EnumWindows(callback, None)
print(f"mmui windows: {len(found)}")
for row in found:
    print(row)

print("\nall weixin.exe visible windows:")
for proc in psutil.process_iter(["pid", "name"]):
    if (proc.info.get("name") or "").lower() != "weixin.exe":
        continue
    pid = proc.info["pid"]

    def cb(hwnd, results):
        if win32gui.IsWindowVisible(hwnd):
            _, p = win32process.GetWindowThreadProcessId(hwnd)
            if p == pid:
                results.append((hwnd, win32gui.GetWindowText(hwnd), win32gui.GetClassName(hwnd)))
    rows = []
    win32gui.EnumWindows(cb, rows)
    for r in rows:
        try:
            uia = desktop.window(handle=r[0]).class_name()
        except Exception:
            uia = "?"
        print(f"  pid={pid} hwnd=0x{r[0]:X} title={r[1]!r} win32={r[2]!r} uia={uia!r}")