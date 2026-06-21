"""通过 wx_key.dll 提取微信数据库密钥并写入 .env。"""

from __future__ import annotations

import ctypes
import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

DLL_CANDIDATES = [
    Path(r"C:\AsusMCenterDownload\wx_key-windows-v2.1.8\data\flutter_assets\assets\dll\wx_key.dll"),
    Path(r"C:\AsusMCenterDownload\wx_key-windows-v2.1.8\wx_key.dll"),
]

ENV_FILE = ROOT / ".env"
POLL_SECONDS = 90


def _find_dll() -> Path:
    for path in DLL_CANDIDATES:
        if path.exists():
            return path
    raise FileNotFoundError(
        "未找到 wx_key.dll，请确认 wx_key 已解压到 C:\\AsusMCenterDownload\\wx_key-windows-v2.1.8"
    )


def _get_weixin_pid() -> int:
    from wxdb import get_wx_info

    info = get_wx_info("v4")
    pid = int(info["pid"])
    print(f"Weixin PID={pid}, version={info.get('version')}, data_dir={info.get('data_dir')}")
    return pid


def _load_api(dll_path: Path):
    lib = ctypes.CDLL(str(dll_path))

    init = lib.InitializeHook
    init.argtypes = [ctypes.c_uint32]
    init.restype = ctypes.c_bool

    poll = lib.PollKeyData
    poll.argtypes = [ctypes.c_char_p, ctypes.c_int]
    poll.restype = ctypes.c_bool

    status = lib.GetStatusMessage
    status.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.POINTER(ctypes.c_int)]
    status.restype = ctypes.c_bool

    cleanup = lib.CleanupHook
    cleanup.argtypes = []
    cleanup.restype = ctypes.c_bool

    last_error = lib.GetLastErrorMsg
    last_error.argtypes = []
    last_error.restype = ctypes.c_char_p

    return init, poll, status, cleanup, last_error


def _normalize_key(key: str) -> str:
    value = key.strip().lower()
    if value.startswith("0x"):
        value = value[2:]
    value = re.sub(r"[^0-9a-f]", "", value)
    if len(value) != 64:
        raise ValueError(f"密钥长度无效: {len(value)}")
    return value


def _write_env_key(key: str) -> None:
    if not ENV_FILE.exists():
        raise FileNotFoundError(f"未找到 {ENV_FILE}")

    lines = ENV_FILE.read_text(encoding="utf-8").splitlines()
    updated = False
    out: list[str] = []
    for line in lines:
        if line.startswith("WECHAT_DB_KEY="):
            out.append(f"WECHAT_DB_KEY={key}")
            updated = True
        else:
            out.append(line)
    if not updated:
        out.append(f"WECHAT_DB_KEY={key}")
    ENV_FILE.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"已写入 {ENV_FILE} -> WECHAT_DB_KEY=***{key[-8:]}")


def main() -> int:
    dll_path = _find_dll()
    print(f"使用 DLL: {dll_path}")

    pid = _get_weixin_pid()
    init, poll, status, cleanup, last_error = _load_api(dll_path)

    if not init(pid):
        err = last_error()
        msg = err.decode("utf-8", errors="replace") if err else "未知错误"
        print(f"InitializeHook 失败: {msg}")
        print("请右键「以管理员身份运行」PowerShell 后重试本脚本，或直接运行 wx_key.exe GUI。")
        return 1

    key_buf = ctypes.create_string_buffer(128)
    log_buf = ctypes.create_string_buffer(512)
    level = ctypes.c_int(0)

    print("Hook 已启动。请在微信里打开任意聊天/滚动消息，触发数据库读取…")
    deadline = time.time() + POLL_SECONDS
    found = ""
    try:
        while time.time() < deadline:
            if poll(key_buf, len(key_buf)):
                found = key_buf.value.decode("utf-8", errors="replace").strip()
                if found:
                    break
            while status(log_buf, len(log_buf), ctypes.byref(level)):
                text = log_buf.value.decode("utf-8", errors="replace").strip()
                if text:
                    print(f"[DLL L{level.value}] {text}")
            time.sleep(0.1)
    finally:
        cleanup()

    if not found:
        print(f"{POLL_SECONDS} 秒内未捕获密钥。请用 wx_key.exe GUI 手动获取。")
        return 1

    key = _normalize_key(found)
    _write_env_key(key)
    print("密钥提取成功。正在验证数据库连接…")

    from app.wechat.db_client import build_wxdb, open_message_connection, resolve_account

    account = resolve_account(key)
    conn = open_message_connection(build_wxdb(account))
    try:
        count = conn.execute("SELECT COUNT(*) FROM MSG").fetchone()[0]
        print(f"验证通过: wxid={account.wxid}, MSG 消息数={count}")
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())