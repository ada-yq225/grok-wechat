import sqlite3
from pathlib import Path

WXID_DIR = Path(r"C:\Users\祁\Documents\xwechat_files\wxid_bnsvdg8hw0tx29_a7d3")
DB_ROOT = WXID_DIR / "db_storage"

for db_path in sorted(DB_ROOT.rglob("*.db"))[:15]:
    print(f"\n=== {db_path.relative_to(WXID_DIR)} ===")
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' LIMIT 8"
        ).fetchall()
        print("tables:", tables)
        conn.close()
    except Exception as exc:
        print("error:", exc)