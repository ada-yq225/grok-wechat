import logging
import sys
from queue import Empty
from threading import Thread

from wcferry import Wcf
from wcferry.wxmsg import WxMsg

from app.config import Settings
from app.grok.client import GrokClient
from app.memory import ConversationMemory
from app.personal.common import RESET_KEYWORDS, split_message
from app.wcf_connect import connect_wcf

logger = logging.getLogger(__name__)


def _extract_text(msg: WxMsg) -> str:
    content = (msg.content or "").strip()
    if msg.from_group() and ":\n" in content:
        return content.split(":\n", 1)[1].strip()
    return content


class PersonalWeChatBot:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._grok = GrokClient(settings)
        self._memory = ConversationMemory(max_turns=settings.max_history_turns)
        self._allowed = settings.allowed_set()
        self._wcf = connect_wcf(
            host=settings.wcf_host,
            port=settings.wcf_port,
            debug=settings.wcf_host is None,
        )
        self._self_wxid = self._wcf.get_self_wxid()

    def run(self) -> None:
        user = self._wcf.get_user_info()
        logger.info("微信已登录: %s (%s)", user.get("name", ""), self._self_wxid)
        logger.info("向机器人发消息即可聊天；发送「重置」清空对话")

        self._wcf.enable_receiving_msg(pyq=False)
        Thread(target=self._message_loop, name="GrokWeChatBot", daemon=True).start()
        self._wcf.keep_running()

    def _message_loop(self) -> None:
        while self._wcf.is_receiving_msg():
            try:
                msg = self._wcf.get_msg()
            except Empty:
                continue
            except Exception:
                logger.exception("接收消息失败")
                continue

            try:
                self._handle_message(msg)
            except Exception:
                logger.exception("处理消息失败: %s", msg)

    def _handle_message(self, msg: WxMsg) -> None:
        if msg.from_self():
            return
        if not msg.is_text():
            return

        sender = msg.sender
        if self._allowed is not None and sender not in self._allowed:
            return

        if msg.from_group():
            if not self._settings.reply_in_group:
                return
            if not msg.is_at(self._self_wxid):
                return

        content = _extract_text(msg)
        if not content:
            return

        receiver = msg.roomid if msg.from_group() else sender
        memory_key = f"{receiver}:{sender}" if msg.from_group() else sender

        if content.lower() in RESET_KEYWORDS or content in RESET_KEYWORDS:
            self._memory.clear(memory_key)
            self._send_text(receiver, "对话已重置，我们可以重新开始。")
            return

        self._send_text(receiver, "正在思考…")
        history = self._memory.get_messages(memory_key)
        answer = self._grok.chat(history, content)

        self._memory.append(memory_key, "user", content)
        self._memory.append(memory_key, "assistant", answer)

        for chunk in split_message(answer):
            self._send_text(receiver, chunk)

    def _send_text(self, receiver: str, text: str) -> None:
        status = self._wcf.send_text(text, receiver)
        if status != 0:
            logger.error("发送消息失败 receiver=%s status=%s", receiver, status)

    def close(self) -> None:
        self._grok.close()


def run_bot(settings: Settings) -> None:
    if sys.platform != "win32" and settings.wcf_host is None:
        logger.error(
            "个人微信机器人需要在 Windows 上运行，并登录 PC 版微信。"
            "如果你在 Mac 上开发，请把代码部署到 Windows 电脑，"
            "或在 .env 中设置 WCF_HOST 连接远程 Windows 上的 WeChatFerry。"
        )
        raise SystemExit(1)

    try:
        bot = PersonalWeChatBot(settings)
    except Exception as exc:
        logger.error("连接微信失败: %s", exc)
        logger.error(
            "常见原因：1) 未登录 PC 微信 3.9.x；2) 误用了 Weixin 4.x；"
            "3) 微信版本与 wcferry 不匹配。运行 scripts\\check_env.py 排查。"
        )
        raise SystemExit(1) from exc

    try:
        bot.run()
    finally:
        bot.close()