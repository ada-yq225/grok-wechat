"""轮询微信本地消息数据库的新消息（支持 Weixin 4.x）。"""

from __future__ import annotations

import logging
import time
from typing import Any

from wxdb import WXDB

from app.wechat.db_client import open_message_connection

logger = logging.getLogger(__name__)

TEXT_MESSAGE_TYPE = 1


def _self_wxid_from_data_dir(data_dir: str) -> str:
    folder = data_dir.rstrip("\\/").split("\\")[-1].split("/")[-1]
    if "_" in folder and folder.startswith("wxid_"):
        return folder.rsplit("_", 1)[0]
    return folder


def _load_name2id(conn) -> dict[int, str]:
    mapping: dict[int, str] = {}
    for rowid, user_name, _is_session in conn.execute(
        "SELECT rowid, user_name, is_session FROM Name2Id"
    ).fetchall():
        mapping[int(rowid)] = (user_name or "").strip()
    return mapping


def _list_msg_tables(conn) -> list[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%' ORDER BY name"
    ).fetchall()
    return [row[0] for row in rows]


def _session_peer_wxid(name2id: dict[int, str], self_rowid: int | None) -> str:
    for rowid, wxid in name2id.items():
        if rowid == self_rowid:
            continue
        if wxid and not wxid.endswith("@chatroom"):
            return wxid
    return ""


def _extract_text_content(raw: Any) -> str:
    if raw is None:
        return ""
    if isinstance(raw, (bytes, bytearray)):
        return ""
    return str(raw).strip()


def _build_v4_event(
    row: tuple[Any, ...],
    *,
    table_name: str,
    name2id: dict[int, str],
    self_rowid: int | None,
) -> dict[str, Any]:
    (
        local_id,
        _server_id,
        local_type,
        _sort_seq,
        real_sender_id,
        create_time,
        *_rest,
    ) = row[:7]
    message_content = row[12] if len(row) > 12 else ""

    sender_rowid = int(real_sender_id)
    sender_wxid = name2id.get(sender_rowid, "")
    peer_wxid = _session_peer_wxid(name2id, self_rowid)
    is_group = peer_wxid.endswith("@chatroom")

    return {
        "id": f"{table_name}:{local_id}",
        "local_id": int(local_id),
        "table": table_name,
        "type": int(local_type),
        "sub_type": 0,
        "is_sender": sender_rowid == self_rowid,
        "create_time": int(create_time),
        "msg": _extract_text_content(message_content),
        "room_wxid": peer_wxid if is_group else None,
        "talker_wxid": peer_wxid or sender_wxid,
        "from_wxid": sender_wxid,
        "to_wxid": None,
    }


def verify_message_database(wx_db: WXDB) -> int:
    """检查消息库可读，返回消息表数量。"""
    conn = open_message_connection(wx_db)
    try:
        tables = _list_msg_tables(conn)
        if not tables:
            raise RuntimeError("未找到 Msg_* 消息表，请确认密钥正确且微信已产生聊天记录")
        return len(tables)
    finally:
        conn.close()


class MessagePoller:
    def __init__(self, wx_db: WXDB, poll_interval: float = 1.0) -> None:
        self._wx_db = wx_db
        self._poll_interval = poll_interval
        self._self_wxid = _self_wxid_from_data_dir(wx_db.data_dir)
        self._self_rowid: int | None = None
        self._name2id: dict[int, str] = {}
        self._last_local_ids: dict[str, int] = {}
        self._bootstrap()

    def _bootstrap(self) -> None:
        conn = open_message_connection(self._wx_db)
        try:
            self._name2id = _load_name2id(conn)
            for rowid, wxid in self._name2id.items():
                if wxid == self._self_wxid:
                    self._self_rowid = rowid
                    break

            for table in _list_msg_tables(conn):
                row = conn.execute(
                    f"SELECT MAX(local_id) FROM [{table}]"
                ).fetchone()
                self._last_local_ids[table] = int(row[0] or 0)
        finally:
            conn.close()

    def poll(self) -> list[dict[str, Any]]:
        conn = open_message_connection(self._wx_db)
        events: list[dict[str, Any]] = []
        try:
            self._name2id = _load_name2id(conn)
            tables = _list_msg_tables(conn)
            for table in tables:
                last_id = self._last_local_ids.get(table, 0)
                rows = conn.execute(
                    f"SELECT * FROM [{table}] WHERE local_id > ? ORDER BY local_id ASC",
                    (last_id,),
                ).fetchall()
                for row in rows:
                    event = _build_v4_event(
                        row,
                        table_name=table,
                        name2id=self._name2id,
                        self_rowid=self._self_rowid,
                    )
                    self._last_local_ids[table] = max(
                        self._last_local_ids.get(table, 0),
                        int(event["local_id"]),
                    )
                    if event["is_sender"]:
                        continue
                    if event["type"] != TEXT_MESSAGE_TYPE:
                        continue
                    if not event["msg"]:
                        continue
                    events.append(event)
        finally:
            conn.close()
        return events

    def run_forever(self, handler) -> None:
        logger.info(
            "开始监听本地数据库新消息 (Weixin 4.x, %d 个会话表)",
            len(self._last_local_ids),
        )
        while True:
            try:
                for event in self.poll():
                    handler(event)
            except Exception:
                logger.exception("轮询微信数据库失败")
            time.sleep(self._poll_interval)