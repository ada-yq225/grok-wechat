"""列出好友 wxid，用于配置 ALLOWED_WXIDS 白名单。"""

import logging
import sys

from wcferry import Wcf

logging.basicConfig(level=logging.INFO, format="%(message)s")


def main() -> None:
    print("连接微信中，请确保 PC 微信 3.9.x 已登录...")
    try:
        wcf = Wcf(debug=True, block=True)
    except Exception as exc:
        print(f"连接失败: {exc}")
        print("请确认已安装并登录 PC 微信 3.9.x（不是 Weixin 4.x）")
        raise SystemExit(1) from exc

    user = wcf.get_user_info()
    print(f"\n当前账号: {user.get('name', '')} ({wcf.get_self_wxid()})\n")
    print(f"{'wxid':<30} {'昵称'}")
    print("-" * 50)
    for friend in wcf.get_friends():
        wxid = friend.get("wxid", "")
        name = friend.get("name", "")
        if wxid and not wxid.endswith("@chatroom"):
            print(f"{wxid:<30} {name}")


if __name__ == "__main__":
    main()