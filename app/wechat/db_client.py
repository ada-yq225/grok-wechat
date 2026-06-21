"""Weixin 4.x 本地数据库访问（基于 wxdb）。"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass

from wxdb import WXDB, get_wx_info

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class WxAccount:
    pid: int
    version: str
    account: str
    data_dir: str
    wxid: str
    key: str


def _normalize_key(key: str) -> str:
    value = key.strip().lower()
    if value.startswith("0x"):
        value = value[2:]
    value = re.sub(r"[^0-9a-f]", "", value)
    if len(value) != 64:
        raise ValueError("WECHAT_DB_KEY 必须是 64 位十六进制字符串")
    return value


def resolve_account(db_key: str | None = None) -> WxAccount:
    info = get_wx_info("v4")
    key = _normalize_key(db_key) if db_key else info.get("key", "")
    if not key or key == "unknown":
        raise RuntimeError(
            "无法自动获取微信数据库密钥。\n"
            "请用 wx_key 工具提取密钥后写入 .env：\n"
            "  WECHAT_DB_KEY=64位十六进制密钥\n"
            "下载：https://github.com/ycccccccy/wx_key/releases"
        )

    data_dir = info["data_dir"].rstrip("\\/")
    wxid = data_dir.split("\\")[-1].split("/")[-1]
    return WxAccount(
        pid=int(info["pid"]),
        version=str(info["version"]),
        account=str(info.get("account", "")),
        data_dir=data_dir,
        wxid=wxid,
        key=key,
    )


def build_wxdb(account: WxAccount) -> WXDB:
    return WXDB(
        pid=account.pid,
        account=account.account,
        key=account.key,
        data_dir=account.data_dir + "\\",
        version=account.version,
    )


def open_message_connection(wx_db: WXDB):
    msg_db = wx_db.get_current_msg_db_name()
    return wx_db.create_connection(rf"db_storage\message\{msg_db}")


def open_contact_connection(wx_db: WXDB):
    return wx_db.create_connection(r"db_storage\contact\contact.db")


def load_contact_labels(wx_db: WXDB) -> dict[str, str]:
    """wxid -> 用于搜索/显示的名称（备注优先）。"""
    labels: dict[str, str] = {}
    conn = open_contact_connection(wx_db)
    try:
        tables = {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        if "contact" not in tables:
            logger.warning("contact.db 中未找到 contact 表")
            return labels

        columns = {
            row[1]
            for row in conn.execute("PRAGMA table_info(contact)").fetchall()
        }
        remark_col = "remark" if "remark" in columns else None
        nick_col = next(
            (c for c in ("nick_name", "nickname", "nickName") if c in columns),
            None,
        )
        username_col = next(
            (c for c in ("username", "user_name", "wxid") if c in columns),
            "username",
        )

        select_cols = [username_col]
        if nick_col:
            select_cols.append(nick_col)
        if remark_col:
            select_cols.append(remark_col)

        query = f"SELECT {', '.join(select_cols)} FROM contact"
        for row in conn.execute(query).fetchall():
            username = (row[0] or "").strip()
            if not username:
                continue
            nick = ""
            remark = ""
            if nick_col and remark_col:
                nick = (row[1] or "").strip()
                remark = (row[2] or "").strip()
            elif nick_col:
                nick = (row[1] or "").strip()
            elif remark_col:
                remark = (row[1] or "").strip()
            label = remark or nick or username
            labels[username] = label
    finally:
        conn.close()
    return labels