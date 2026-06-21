import ctypes

user32 = ctypes.windll.user32
dc = user32.GetDC(0)
dpi = ctypes.windll.gdi32.GetDeviceCaps(dc, 88)
user32.ReleaseDC(0, dc)
print(f"DPI={dpi} scale={dpi/96*100:.0f}%")