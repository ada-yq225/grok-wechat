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
print("msg_db:", msg_db)
conn = db.create_connection(rf"db_storage\message\{msg_db}")
tables = conn.execute(
    "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
).fetchall()
print("tables:", [t[0] for t in tables])
for name in [t[0] for t in tables]:
    try:
        count = conn.execute(f"SELECT COUNT(*) FROM [{name}]").fetchone()[0]
        print(f"  {name}: {count}")
    except Exception as exc:
        print(f"  {name}: {exc}")
conn.close()