import json
import tempfile
from pathlib import Path

from pywxdump.db.dbMSG import MsgHandler
from pywxdump.wx_core.merge_db import merge_real_time_db
from pywxdump.wx_core.wx_info import get_wx_db, get_wx_info

print("=== get_wx_info ===")
infos = get_wx_info(WX_OFFS={}, is_print=False)
print(json.dumps(infos, ensure_ascii=False, indent=2)[:4000])

if not infos:
    raise SystemExit("get_wx_info failed")

info = infos[0] if isinstance(infos, list) else infos
print("\nkeys:", list(info.keys()) if isinstance(info, dict) else type(info))

print("\n=== get_wx_db ===")
dbs = get_wx_db(info.get("wxid", ""), info.get("wx_dir", ""))
print("db count:", len(dbs) if dbs else 0)
if dbs:
    for item in dbs[:8]:
        print(" ", item)

tmpdir = Path(tempfile.mkdtemp(prefix="grok-wechat-db-"))
print("\n=== merge_real_time_db ===")
print("tmpdir:", tmpdir)
try:
    out = merge_real_time_db(
        key=info.get("key"),
        wx_path=info.get("wx_dir"),
        merge_path=str(tmpdir),
        is_merge_data=True,
        is_del_decrypted=False,
    )
    print("merge result:", out)
    candidates = list(tmpdir.rglob("*.db"))
    print("db files:", [str(p.name) for p in candidates[:15]])
    msg_candidates = [p for p in candidates if "MSG" in p.name.upper() or "message" in p.name.lower()]
    msg_db = msg_candidates[0] if msg_candidates else (candidates[0] if candidates else None)
    if msg_db and msg_db.exists():
        handler = MsgHandler(str(msg_db))
        rows, cols = handler.get_msg_list(page_size=10)
        print("message columns sample:", cols[:8] if cols else None)
        print("latest messages:")
        for row in rows[-5:]:
            print(" ", {k: row.get(k) for k in ("id", "talker", "room_name", "msg", "is_sender", "CreateTime") if k in row})
except Exception as exc:
    import traceback
    traceback.print_exc()