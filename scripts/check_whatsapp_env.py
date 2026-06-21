"""检查 WhatsApp 机器人运行环境。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

ENV_FILE = ROOT / ".env"


def _read_env_value(key: str, default: str = "") -> str:
    if not ENV_FILE.exists():
        return default
    for line in ENV_FILE.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if stripped.startswith("#") or "=" not in stripped:
            continue
        name, value = stripped.split("=", 1)
        if name.strip() == key:
            return value.strip()
    return default


def _ok(message: str) -> None:
    print(f"  [OK] {message}")


def _fail(message: str) -> None:
    print(f"  [XX] {message}")


def main() -> int:
    print("=== Grok WhatsApp 环境检查 ===\n")
    ok = True

    print("[配置]")
    if not ENV_FILE.exists():
        _fail(".env 不存在")
        ok = False
    else:
        key = _read_env_value("XAI_API_KEY", "")
        if not key or key == "your_xai_api_key":
            _fail("XAI_API_KEY 未配置")
            ok = False
        else:
            _ok("XAI_API_KEY 已配置")
        session = _read_env_value("WHATSAPP_SESSION_NAME", "grok-whatsapp")
        _ok(f"会话名: {session}")

    print("\n[依赖]")
    try:
        import neonize

        _ok(f"neonize {neonize.__version__}")
    except ImportError:
        _fail("缺少 neonize，请运行 pip install -r requirements.txt")
        ok = False

    print("\n[说明]")
    print("  WhatsApp 机器人在后台运行，不依赖 PC 微信客户端。")
    print("  首次启动会显示 QR 码，用手机 WhatsApp → 设置 → 关联设备 扫描。")
    print("  登录后即使关闭 WhatsApp 网页，进程保持运行即可继续收消息。")

    print()
    if ok:
        print("检查通过。运行: .venv\\Scripts\\python run_whatsapp.py")
        print("或双击: 启动WhatsApp机器人.bat")
        return 0
    print("部分检查未通过，请修复后再启动。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())