"""WhatsApp 后台机器人（neonize / WhatsApp Web 多设备）。"""

from __future__ import annotations

import logging
import re
import threading
from collections import deque
from pathlib import Path

from neonize import NewClient
from neonize.events import ConnectedEv, MessageEv, PairStatusEv
from neonize.proto.Neonize_pb2 import Message as WaMessageEv
from neonize.utils.jid import Jid2String
from neonize.utils.message import extract_text

from app.config import Settings
from app.grok.client import GrokClient
from app.memory import ConversationMemory
from app.personal.common import RESET_KEYWORDS, split_message

logger = logging.getLogger(__name__)


def _normalize_phone(value: str) -> str:
    return re.sub(r"\D", "", value.strip())


def _chat_key(message: WaMessageEv) -> str:
    source = message.Info.MessageSource
    return Jid2String(source.Chat)


def _sender_label(message: WaMessageEv) -> str:
    source = message.Info.MessageSource
    sender = source.SenderAlt if source.SenderAlt.ListFields() else source.Sender
    label = Jid2String(sender)
    user = sender.User
    if user:
        return user
    return label


class WhatsAppGrokBot:
    def __init__(self, settings: Settings, session_dir: Path) -> None:
        self._settings = settings
        self._session_dir = session_dir
        self._grok = GrokClient(settings)
        self._memory = ConversationMemory(max_turns=settings.max_history_turns)
        allowed = settings.allowed_whatsapp_set()
        self._allowed = (
            {_normalize_phone(item) for item in allowed} if allowed is not None else None
        )
        self._handler_lock = threading.Lock()
        self._own_user = ""
        self._recent_outgoing: deque[str] = deque(maxlen=30)
        session_name = settings.whatsapp_session_name.strip() or "grok-whatsapp"
        self._client = NewClient(name=session_name)
        self._qr_image = session_dir.parent.parent / "whatsapp_qr.png"
        self._setup_qr_handler()
        self._register_handlers()

    def _setup_qr_handler(self) -> None:
        def on_qr(_client: NewClient, data: bytes) -> None:
            import os
            import sys

            import segno

            qr = segno.make_qr(data)
            qr.save(str(self._qr_image))
            logger.info("请扫描 QR 码登录（已保存图片: %s）", self._qr_image)
            if sys.platform == "win32" and not _client.connected:
                try:
                    os.startfile(self._qr_image)
                except OSError:
                    logger.info("无法自动打开图片，请手动打开 whatsapp_qr.png")
            try:
                qr.terminal(compact=True)
            except Exception:
                logger.info("终端无法显示 QR，请直接打开图片文件扫描")

        self._client.qr(on_qr)

    def _register_handlers(self) -> None:
        @self._client.event(PairStatusEv)
        def on_pair(_client: NewClient, event) -> None:
            logger.info("配对状态: %s", event)

        @self._client.event(ConnectedEv)
        def on_connected(client: NewClient, _event) -> None:
            if client.me and client.me.JID.ListFields():
                self._own_user = client.me.JID.User
            logger.info("WhatsApp 已连接，等待消息…")
            if self._qr_image.exists():
                try:
                    self._qr_image.unlink()
                except OSError:
                    pass

        @self._client.event(MessageEv)
        def on_message(client: NewClient, message: WaMessageEv) -> None:
            threading.Thread(
                target=self._handle_message,
                args=(client, message),
                daemon=True,
            ).start()

    def _is_self_chat(self, source) -> bool:
        if not self._own_user:
            return False
        return source.Chat.User == self._own_user

    def _handle_message(self, client: NewClient, message: WaMessageEv) -> None:
        with self._handler_lock:
            if not self._own_user and client.me and client.me.JID.ListFields():
                self._own_user = client.me.JID.User

            source = message.Info.MessageSource
            is_self_chat = self._is_self_chat(source)

            if source.IsFromMe:
                if not (is_self_chat and self._settings.whatsapp_reply_to_self):
                    return
            elif source.IsGroup and not self._settings.whatsapp_reply_in_group:
                return

            text = (extract_text(message.Message) or "").strip()
            if not text:
                return

            if source.IsFromMe and text in self._recent_outgoing:
                try:
                    self._recent_outgoing.remove(text)
                except ValueError:
                    pass
                return

            sender = _sender_label(message)
            chat_key = _chat_key(message)
            sender_phone = _normalize_phone(sender)

            if (
                self._allowed is not None
                and sender_phone not in self._allowed
                and not is_self_chat
            ):
                logger.debug("跳过未授权联系人: %s", sender)
                return

            label = "自己" if is_self_chat else sender
            logger.info("收到 WhatsApp %s: %s", label, text[:80])

            if text.lower() in RESET_KEYWORDS or text in RESET_KEYWORDS:
                self._memory.clear(chat_key)
                self._send_reply(client, source.Chat, ["对话已重置，我们可以重新开始。"])
                return

            history = self._memory.get_messages(chat_key)
            answer = self._grok.chat(history, text)
            self._memory.append(chat_key, "user", text)
            self._memory.append(chat_key, "assistant", answer)
            self._send_reply(client, source.Chat, split_message(answer))

    def _send_reply(self, client: NewClient, chat, chunks: list[str]) -> None:
        for chunk in chunks:
            if chunk:
                self._recent_outgoing.append(chunk)
                client.send_message(chat, chunk)

    def run(self) -> None:
        self._session_dir.mkdir(parents=True, exist_ok=True)
        logger.info("WhatsApp 会话目录: %s", self._session_dir)
        logger.info("首次运行请在终端扫描 QR 码（WhatsApp → 关联设备）")
        logger.info("私聊或「发给自己」即可与 Grok 对话；发送「重置」清空记忆")
        if self._allowed is not None:
            logger.info("白名单号码: %s", ", ".join(sorted(self._allowed)))
        self._client.connect()

    def close(self) -> None:
        try:
            self._client.disconnect()
        except Exception:
            logger.debug("断开 WhatsApp 连接时出错", exc_info=True)
        self._grok.close()


def run_whatsapp_bot(settings: Settings) -> None:
    root = Path(__file__).resolve().parents[2]
    session_dir = root / "data" / "whatsapp"
    session_dir.mkdir(parents=True, exist_ok=True)
    bot = WhatsAppGrokBot(settings, session_dir)
    try:
        import os

        os.chdir(session_dir)
        bot.run()
    finally:
        bot.close()