"""Weixin 4.x 机器人：数据库监听 + 键盘发消息。"""

from __future__ import annotations

import logging
import sys
import threading

from app.config import Settings
from app.grok.client import GrokClient
from app.memory import ConversationMemory
from app.personal.common import RESET_KEYWORDS, split_message
from app.wechat.db_client import build_wxdb, load_contact_labels, resolve_account
from app.wechat.db_listener import MessagePoller
from app.wechat import keyboard as wx_keyboard

logger = logging.getLogger(__name__)


class DbKeyboardGrokBot:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._grok = GrokClient(settings)
        self._memory = ConversationMemory(max_turns=settings.max_history_turns)
        self._allowed = settings.allowed_friends_set()
        self._send_lock = threading.Lock()
        self._account = resolve_account(settings.wechat_db_key or None)
        self._wx_db = build_wxdb(self._account)
        self._contact_labels = load_contact_labels(self._wx_db)
        self._poller = MessagePoller(self._wx_db, poll_interval=settings.db_poll_interval_sec)

    def run(self) -> None:
        logger.info(
            "微信已登录: %s [Weixin %s, 模式=db_keyboard]",
            self._account.wxid,
            self._account.version,
        )
        logger.info("监听数据库新消息；发送时请勿操作鼠标键盘")
        logger.info("向机器人发私聊即可聊天；发送「重置」清空对话")
        self._poller.run_forever(self._handle_event)

    def _handle_event(self, event: dict) -> None:
        if event.get("room_wxid") and not self._settings.reply_in_group:
            return

        talker_wxid = event.get("talker_wxid") or event.get("from_wxid") or ""
        memory_key = talker_wxid or event.get("from_wxid") or "unknown"
        friend_label = self._resolve_label(talker_wxid, event.get("from_wxid"))

        if self._allowed is not None:
            allowed = {*self._allowed, *(self._contact_labels.get(w, w) for w in self._allowed)}
            if friend_label not in allowed and talker_wxid not in allowed:
                logger.debug("跳过未授权联系人: %s", friend_label)
                return

        content = (event.get("msg") or "").strip()
        if not content:
            return

        logger.info("收到 %s: %s", friend_label, content[:80])

        if content.lower() in RESET_KEYWORDS or content in RESET_KEYWORDS:
            self._memory.clear(memory_key)
            self._send_reply(friend_label, ["对话已重置，我们可以重新开始。"])
            return

        history = self._memory.get_messages(memory_key)
        answer = self._grok.chat(history, content)
        self._memory.append(memory_key, "user", content)
        self._memory.append(memory_key, "assistant", answer)
        self._send_reply(friend_label, split_message(answer))

    def _resolve_label(self, talker_wxid: str, from_wxid: str | None) -> str:
        for wxid in (talker_wxid, from_wxid or ""):
            if wxid and wxid in self._contact_labels:
                return self._contact_labels[wxid]
        return talker_wxid or from_wxid or "unknown"

    def _send_reply(self, friend_label: str, chunks: list[str]) -> None:
        if not chunks:
            return
        with self._send_lock:
            try:
                if len(chunks) == 1:
                    wx_keyboard.send_messages_to_friend(friend_label, chunks)
                    return
                wx_keyboard.send_messages_to_friend(friend_label, chunks[:-1])
                wx_keyboard.send_messages_to_friend(friend_label, [chunks[-1]])
            except Exception:
                logger.exception("键盘发送消息失败: %s", friend_label)

    def close(self) -> None:
        self._grok.close()


def run_db_keyboard_bot(settings: Settings) -> None:
    if sys.platform != "win32":
        logger.error("个人微信机器人需要在 Windows 上运行。")
        raise SystemExit(1)

    bot = DbKeyboardGrokBot(settings)
    try:
        bot.run()
    finally:
        bot.close()