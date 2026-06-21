"""通过快捷键向微信好友发送消息（不依赖 UI 控件树）。"""

from __future__ import annotations

import logging
import time

import pyautogui
import pyperclip
import win32con
import win32gui

logger = logging.getLogger(__name__)

pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05


def _find_weixin_hwnd() -> int:
    hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
    if hwnd == 0:
        hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "Weixin")
    return hwnd


def focus_weixin() -> int:
    hwnd = _find_weixin_hwnd()
    if hwnd == 0:
        raise RuntimeError("未找到微信窗口，请先打开并登录微信")
    if win32gui.IsIconic(hwnd):
        win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
    try:
        win32gui.SetForegroundWindow(hwnd)
    except Exception:
        win32gui.BringWindowToTop(hwnd)
    time.sleep(0.25)
    return hwnd


def send_messages_to_friend(
    friend_label: str,
    messages: list[str],
    *,
    search_delay: float = 0.35,
    send_delay: float = 0.2,
) -> None:
    if not friend_label:
        raise ValueError("friend_label 不能为空")
    if not messages:
        return

    focus_weixin()
    pyautogui.hotkey("ctrl", "f")
    time.sleep(search_delay)

    pyperclip.copy(friend_label)
    pyautogui.hotkey("ctrl", "a")
    pyautogui.hotkey("ctrl", "v")
    time.sleep(search_delay)
    pyautogui.press("enter")
    time.sleep(search_delay)

    for message in messages:
        pyperclip.copy(message)
        pyautogui.hotkey("ctrl", "v")
        time.sleep(0.05)
        pyautogui.press("enter")
        time.sleep(send_delay)

    logger.info("已通过键盘发送 %d 条消息给 %s", len(messages), friend_label)