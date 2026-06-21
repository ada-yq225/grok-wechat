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

print("=== Name2Id ===")
cols = conn.execute("PRAGMA table_info(Name2Id)").fetchall()
print("columns:", [c[1] for c in cols])
for row in conn.execute("SELECT * FROM Name2Id").fetchall():
    print(" ", row)

print("\n=== TimeStamp ===")
cols = conn.execute("PRAGMA table_info(TimeStamp)").fetchall()
print("columns:", [c[1] for c in cols])
for row in conn.execute("SELECT * FROM TimeStamp").fetchall():
    print(" ", row)

tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'"
).fetchall()
for (table,) in tables:
    print(f"\n=== {table} ===")
    cols = conn.execute(f"PRAGMA table_info([{table}])").fetchall()
    print("columns:", [c[1] for c in cols])
    rows = conn.execute(f"SELECT * FROM [{table}] ORDER BY 1 DESC LIMIT 3").fetchall()
    for row in rows:
        print(" ", row[:10], "...")

conn.close()