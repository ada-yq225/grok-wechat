"""Weixin 4.x 机器人（基于 pyweixin UI 自动化）。"""

from __future__ import annotations

import logging
import sys
import time

from pyweixin.Config import GlobalConfig
from pyweixin.WeChatAuto import AutoReply, Messages
from pyweixin.WeChatTools import Navigator, Tools
from pyweixin.utils import scan_for_new_messages

from app.config import Settings
from app.grok.client import GrokClient
from app.memory import ConversationMemory
from app.personal.common import RESET_KEYWORDS, split_message

logger = logging.getLogger(__name__)

POLL_INTERVAL_SEC = 3
LISTEN_DURATION = "30s"


class WeixinGrokBot:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._grok = GrokClient(settings)
        self._memory = ConversationMemory(max_turns=settings.max_history_turns)
        self._allowed = settings.allowed_friends_set()
        self._main_window = None
        self._self_info: dict | None = None

    def run(self) -> None:
        GlobalConfig.close_weixin = False
        GlobalConfig.is_maximize = False
        GlobalConfig.search_pages = 0

        if not Tools.is_weixin_running():
            raise RuntimeError(
                "Weixin 4.x 未运行。请先打开新版微信并登录你的小号。"
            )

        self._self_info = Tools.about_weixin()
        logger.info(
            "微信已登录: wxid=%s [Weixin %s]",
            self._self_info.get("wxid", ""),
            self._self_info.get("版本", ""),
        )
        logger.info("正在监听新消息，向机器人发私聊即可聊天；发送「重置」清空对话")

        self._main_window = Navigator.open_weixin(is_maximize=False)

        while True:
            try:
                self._poll_once()
            except Exception:
                logger.exception("处理消息轮询失败")
            time.sleep(POLL_INTERVAL_SEC)

    def _poll_once(self) -> None:
        assert self._main_window is not None
        pending = scan_for_new_messages(
            main_window=self._main_window,
            close_weixin=False,
        )
        if not pending:
            return

        for friend, count in pending.items():
            if count <= 0:
                continue
            if self._allowed is not None and friend not in self._allowed:
                logger.debug("跳过未授权联系人: %s", friend)
                continue
            try:
                self._handle_friend(friend)
            except Exception:
                logger.exception("处理 %s 的消息失败", friend)

    def _handle_friend(self, friend: str) -> None:
        dialog = Navigator.open_dialog_window(
            friend=friend,
            is_maximize=False,
            search_pages=0,
        )
        if Tools.is_group_chat(dialog) and not self._settings.reply_in_group:
            logger.debug("跳过群聊: %s", friend)
            return

        callback = self._make_callback(friend)
        AutoReply.auto_reply_to_friend(
            dialog_window=dialog,
            duration=LISTEN_DURATION,
            callback=callback,
            close_dialog_window=False,
        )

    def _make_callback(self, friend: str):
        def callback(new_message: str, _contexts: list[str]) -> str | None:
            content = (new_message or "").strip()
            if not content:
                return None

            memory_key = friend
            if content.lower() in RESET_KEYWORDS or content in RESET_KEYWORDS:
                self._memory.clear(memory_key)
                return "对话已重置，我们可以重新开始。"

            history = self._memory.get_messages(memory_key)
            answer = self._grok.chat(history, content)
            self._memory.append(memory_key, "user", content)
            self._memory.append(memory_key, "assistant", answer)

            chunks = split_message(answer)
            if len(chunks) == 1:
                return chunks[0]

            Messages.send_messages_to_friend(
                friend=friend,
                messages=chunks[:-1],
                close_weixin=False,
                search_pages=0,
            )
            return chunks[-1]

        return callback

    def close(self) -> None:
        self._grok.close()


def run_weixin_bot(settings: Settings) -> None:
    if sys.platform != "win32":
        logger.error("个人微信机器人需要在 Windows 上运行。")
        raise SystemExit(1)

    bot = WeixinGrokBot(settings)
    try:
        bot.run()
    finally:
        bot.close()