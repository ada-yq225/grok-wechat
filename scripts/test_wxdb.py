import json

try:
    from wxdb import get_wx_db, get_wx_info
except ImportError as exc:
    print("import error:", exc)
    raise

print("=== get_wx_info ===")
try:
    info = get_wx_info()
    print(json.dumps(info, ensure_ascii=False, indent=2, default=str))
except Exception as exc:
    print("get_wx_info failed:", type(exc).__name__, exc)
    info = None

if info:
    print("\n=== get_wx_db v4 ===")
    try:
        wx_db = get_wx_db("v4")
        msg_name = wx_db.get_current_msg_db_name()
        print("msg db:", msg_name)
        conn = wx_db.create_connection(rf"db_storage\message\{msg_name}")
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' LIMIT 20"
        ).fetchall()
        print("tables:", tables)
        for table in ("MSG", "Name2Id", "Name2ID", "Message", "message"):
            try:
                count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
                print(f"  {table} count:", count)
            except Exception:
                pass
        try:
            rows = conn.execute(
                "SELECT * FROM MSG ORDER BY CreateTime DESC LIMIT 3"
            ).fetchall()
            print("latest MSG rows:", len(rows))
            for row in rows:
                print(" ", row[:8] if isinstance(row, tuple) else row)
        except Exception as exc:
            print("MSG query failed:", exc)
        conn.close()
    except Exception as exc:
        import traceback
        traceback.print_exc()