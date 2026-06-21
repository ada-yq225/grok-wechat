"""启动前环境检查。"""

from __future__ import annotations

import logging
import platform
import subprocess
from pathlib import Path

from app.config import Settings

logger = logging.getLogger(__name__)

WECHAT39_DOWNLOAD = (
    "https://github.com/tom-snow/wechat-windows-versions/releases/tag/v3.9.12.51"
)


def _is_process_running(name: str) -> bool:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Process -Name {name} -ErrorAction SilentlyContinue | "
                f"Measure-Object).Count -gt 0",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip().lower() == "true"
    except OSError:
        return False


def _count_real_mmui(window) -> int:
    count = 0

    def walk(elem, depth: int = 0) -> None:
        nonlocal count
        if depth > 12:
            return
        try:
            cls = elem.class_name()
            if cls.startswith("mmui::"):
                count += 1
            for child in elem.children():
                walk(child, depth + 1)
        except Exception:
            return

    walk(window)
    return count


def _weixin_ui_ready() -> bool:
    try:
        import win32gui
        from pywinauto import Desktop
    except ImportError:
        return False

    hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
    if hwnd == 0:
        hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "Weixin")
    if hwnd == 0:
        return False
    window = Desktop(backend="uia").window(handle=hwnd)
    return (
        window.class_name() == "mmui::MainWindow"
        or _count_real_mmui(window) > 0
    )


def _validate_pyweixin() -> None:
    try:
        from pyweixin.WeChatTools import Tools
    except ImportError as exc:
        raise SystemExit(
            "未安装 pywechat127。请运行: .venv\\Scripts\\pip install pywechat127"
        ) from exc

    if not Tools.is_weixin_running():
        raise SystemExit(
            "Weixin 4.x 未运行。\n"
            "请先打开新版微信（Weixin.exe）并用小号登录，再启动机器人。"
        )

    info = Tools.about_weixin()
    logger.info(
        "检测到 Weixin %s，wxid=%s",
        info.get("版本", ""),
        info.get("wxid", ""),
    )

    if not _weixin_ui_ready():
        raise SystemExit(
            "微信 UI 尚未开启无障碍，pyweixin 无法操作界面。\n"
            "若讲述人已先运行 5+ 分钟仍失败，可能是该账号被微信限制 UIAutomation。\n"
            "请尝试：\n"
            "  1. 重启电脑 → 讲述人 10 分钟 → 再登录\n"
            "  2. 先登录另一个微信号，再切回小号\n"
            "  3. 运行诊断: .venv\\Scripts\\python scripts\\diagnose_all.py"
        )


def _validate_db_keyboard(settings: Settings) -> None:
    try:
        import win32gui
    except ImportError as exc:
        raise SystemExit(
            "未安装 pywin32。请运行: .venv\\Scripts\\pip install pywin32"
        ) from exc

    if not _is_process_running("Weixin"):
        raise SystemExit(
            "Weixin 4.x 未运行。\n"
            "请先打开新版微信（Weixin.exe）并用小号登录，再启动机器人。"
        )

    hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
    if hwnd == 0:
        hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "Weixin")
    if hwnd == 0:
        raise SystemExit(
            "未找到微信窗口。请保持微信已登录且窗口未完全退出。"
        )

    if not settings.wechat_db_key.strip():
        raise SystemExit(
            "请在 .env 中配置 WECHAT_DB_KEY（64 位十六进制密钥）。\n"
            "下载 wx_key 提取密钥: https://github.com/ycccccccy/wx_key/releases\n"
            "注意：wx_key 安装路径不要包含中文。"
        )

    try:
        from app.wechat.db_client import build_wxdb, resolve_account
        from app.wechat.db_listener import verify_message_database
    except ImportError as exc:
        raise SystemExit(
            "未安装 wxdb。请运行: .venv\\Scripts\\pip install wxdb>=0.0.9"
        ) from exc

    account = resolve_account(settings.wechat_db_key)
    logger.info(
        "检测到 Weixin %s，wxid=%s [db_keyboard]",
        account.version,
        account.wxid,
    )

    wx_db = build_wxdb(account)
    try:
        table_count = verify_message_database(wx_db)
        logger.info("消息数据库可读，会话表数=%s", table_count)
    except Exception as exc:
        raise SystemExit(
            "无法读取微信本地数据库，请确认 WECHAT_DB_KEY 正确且微信已登录。\n"
            f"详情: {exc}"
        ) from exc


def _validate_wcferry() -> None:
    wechat39 = [
        Path(r"C:\Program Files\Tencent\WeChat\WeChat.exe"),
        Path(r"C:\Program Files (x86)\Tencent\WeChat\WeChat.exe"),
        Path(__file__).resolve().parents[1] / "wechat39" / "WeChat.exe",
    ]
    wechat39 = [p for p in wechat39 if p.exists()]

    if not _is_process_running("WeChat"):
        if _is_process_running("Weixin"):
            raise SystemExit(
                "wcferry 模式需要 PC 微信 3.9，当前运行的是 Weixin 4.x。\n"
                "请改用新版微信：在 .env 设置 WECHAT_BACKEND=pyweixin"
            )
        raise SystemExit(
            "PC 微信 3.9 未运行。\n"
            r'请打开 "C:\Program Files\Tencent\WeChat\WeChat.exe" 并登录。'
            f"\n或改用新版微信：WECHAT_BACKEND=pyweixin\n"
            f"下载 3.9: {WECHAT39_DOWNLOAD}"
        )

    if not wechat39:
        logger.warning("未在常见路径找到 WeChat.exe，请确认已安装 PC 微信 3.9.x")


def validate_startup(settings: Settings) -> None:
    if platform.system() != "Windows" and settings.wcf_host is None:
        raise SystemExit(
            "个人微信机器人需要在 Windows 上运行。"
            "若在 Mac 开发，请部署到 Windows 或在 .env 设置 WCF_HOST。"
        )

    if not settings.xai_api_key or settings.xai_api_key == "your_xai_api_key":
        raise SystemExit(
            "请在 .env 中配置 XAI_API_KEY（https://console.x.ai/）"
        )

    backend = settings.wechat_backend.strip().lower()
    if backend == "db_keyboard":
        _validate_db_keyboard(settings)
    elif backend == "pyweixin":
        _validate_pyweixin()
    elif backend == "wcferry":
        _validate_wcferry()
    else:
        raise SystemExit(
            f"未知的 WECHAT_BACKEND={settings.wechat_backend}，"
            "请使用 db_keyboard、pyweixin 或 wcferry"
        )