import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.wechat.db_client import build_wxdb, resolve_account

s = get_settings()
acc = resolve_account(s.wechat_db_key)
db = build_wxdb(acc)
msg_db = db.get_current_msg_db_name()
conn = db.create_connection(rf"db_storage\message\{msg_db}")

table = "Msg_2bafa8eefa0843ab78c69c0ebc3ee9e7"
cols = [c[1] for c in conn.execute(f"PRAGMA table_info([{table}])").fetchall()]
row = conn.execute(f"SELECT * FROM [{table}] ORDER BY local_id DESC LIMIT 1").fetchone()
print("columns:", cols)
for c, v in zip(cols, row):
    if isinstance(v, (bytes, bytearray)):
        print(f"  {c}: <bytes len={len(v)}>")
    else:
        print(f"  {c}: {v!r}")

conn.close()