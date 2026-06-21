import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.wechat.db_client import build_wxdb, resolve_account

s = get_settings()
acc = resolve_account(s.wechat_db_key)
db = build_wxdb(acc)
conn = db.create_connection(r"db_storage\message\message_0.db")

print("Name2Id:")
for i, row in enumerate(conn.execute("SELECT rowid, user_name, is_session FROM Name2Id").fetchall()):
    print(f"  rowid={row[0]} {row[1:]}")

table = "Msg_2bafa8eefa0843ab78c69c0ebc3ee9e7"
print(f"\n{table} sample:")
rows = conn.execute(
    f"SELECT local_id, local_type, real_sender_id, create_time, message_content, status "
    f"FROM [{table}] ORDER BY local_id DESC LIMIT 15"
).fetchall()
for r in rows:
    print(r)

conn.close()