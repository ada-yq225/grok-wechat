"""主动向指定好友发送消息（键盘模拟）。"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.wechat import keyboard as wx_keyboard
from app.wechat.db_client import build_wxdb, load_contact_labels, resolve_account
from app.config import get_settings


def main() -> int:
    parser = argparse.ArgumentParser(description="向微信好友主动发消息")
    parser.add_argument("friend", nargs="?", help="好友备注/昵称，留空则发给最近会话好友")
    parser.add_argument(
        "-m",
        "--message",
        default="你好！这是 Grok 微信机器人的测试消息，收到请回复我～",
        help="要发送的文本",
    )
    args = parser.parse_args()

    settings = get_settings()
    account = resolve_account(settings.wechat_db_key)
    labels = load_contact_labels(build_wxdb(account))

    friend_label = args.friend
    if not friend_label:
        # 最近有聊天记录的好友（排除系统号）
        from app.wechat.db_client import open_message_connection
        from app.wechat.db_listener import _load_name2id

        wx_db = build_wxdb(account)
        conn = open_message_connection(wx_db)
        try:
            name2id = _load_name2id(conn)
            self_prefix = account.wxid.rsplit("_", 1)[0]
            for _rowid, wxid in name2id.items():
                if wxid and wxid != self_prefix and not wxid.endswith("@chatroom"):
                    friend_label = labels.get(wxid, wxid)
                    break
        finally:
            conn.close()

    if not friend_label:
        print("未找到可发送的好友，请指定: python scripts/send_to_friend.py 好友昵称")
        return 1

    print(f"即将发送给: {friend_label}")
    print(f"内容: {args.message}")
    print("请勿操作鼠标键盘…")
    wx_keyboard.send_messages_to_friend(friend_label, [args.message])
    print("发送完成")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())