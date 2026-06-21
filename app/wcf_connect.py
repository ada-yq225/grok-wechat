"""带超时的 WeChatFerry 连接。"""

from __future__ import annotations

import logging
import threading
import time
from typing import Any

from wcferry import Wcf

logger = logging.getLogger(__name__)

INIT_TIMEOUT_SEC = 30
LOGIN_TIMEOUT_SEC = 90


def _create_wcf(
    *,
    host: str | None,
    port: int,
    debug: bool,
    holder: dict[str, Any],
) -> None:
    try:
        holder["wcf"] = Wcf(host=host, port=port, debug=debug, block=False)
    except Exception as exc:
        holder["error"] = exc


def connect_wcf(
    *,
    host: str | None,
    port: int,
    debug: bool,
    init_timeout: int = INIT_TIMEOUT_SEC,
    login_timeout: int = LOGIN_TIMEOUT_SEC,
) -> Wcf:
    logger.info("正在连接 WeChatFerry…")
    holder: dict[str, Any] = {}
    thread = threading.Thread(
        target=_create_wcf,
        kwargs={
            "host": host,
            "port": port,
            "debug": debug,
            "holder": holder,
        },
        daemon=True,
    )
    thread.start()
    thread.join(timeout=init_timeout)

    if thread.is_alive():
        raise RuntimeError(
            f"WeChatFerry 在 {init_timeout} 秒内未能完成初始化。\n"
            "常见原因：\n"
            "  1. PC 微信未打开或未登录\n"
            "  2. 杀毒软件拦截了 wcferry 注入\n"
            "  3. 需要以管理员身份运行 PowerShell\n"
            "建议：先登录微信，再右键「以管理员身份运行」启动机器人.bat"
        )

    if "error" in holder:
        raise RuntimeError(f"WeChatFerry 初始化失败: {holder['error']}") from holder["error"]

    wcf = holder.get("wcf")
    if wcf is None:
        raise RuntimeError("WeChatFerry 初始化失败，未返回连接对象。")

    logger.info("等待微信登录（最多 %d 秒）…", login_timeout)
    deadline = time.monotonic() + login_timeout
    while time.monotonic() < deadline:
        try:
            if wcf.is_login():
                return wcf
        except Exception:
            pass
        time.sleep(1)

    raise RuntimeError(
        f"微信在 {login_timeout} 秒内未完成登录。\n"
        "请确认：\n"
        r'  1. 已打开 "C:\Program Files\Tencent\WeChat\WeChat.exe"' + "\n"
        "  2. 已用小号扫码登录（窗口里能看到聊天列表，不是停在扫码页）\n"
        "  3. 登录成功后再启动机器人"
    )