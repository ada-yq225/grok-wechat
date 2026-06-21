"""检查 grok-wechat 运行环境是否就绪。"""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
ENV_FILE = ROOT / ".env"
ENV_EXAMPLE = ROOT / ".env.example"

WECHAT39_HINT = (
    "WeChatFerry 需要 PC 微信 3.9.x（WeChat.exe），不支持新版 Weixin 4.x。"
    "运行 scripts\\install_wechat39.ps1 安装 3.9.12.51，"
    "或从 https://github.com/tom-snow/wechat-windows-versions/releases/tag/v3.9.12.51 手动下载。"
)


def _ok(message: str) -> None:
    print(f"  [OK] {message}")


def _warn(message: str) -> None:
    print(f"  [!!] {message}")


def _fail(message: str) -> None:
    print(f"  [XX] {message}")


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


def _is_process_running(name: str) -> bool:
    try:
        result = subprocess.run(
            [
                "powershell",
                "-NoProfile",
                "-Command",
                f"(Get-Process -Name {name} -ErrorAction SilentlyContinue | "
                f"Measure-Object).Count -gt 0",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        return result.stdout.strip().lower() == "true"
    except OSError:
        return False


def check_python() -> bool:
    version = sys.version_info
    print(f"Python {version.major}.{version.minor}.{version.micro}")
    if version.major == 3 and version.minor >= 10:
        _ok("Python 版本可用")
        return True
    _warn("建议使用 Python 3.10–3.12；当前版本可能兼容")
    return True


def check_platform() -> bool:
    print(f"系统: {platform.system()} {platform.release()}")
    if platform.system() != "Windows":
        _fail("个人微信机器人必须在 Windows 上运行（或设置 WCF_HOST 连接远程 Windows）")
        return False
    _ok("Windows 环境")
    return True


def check_dependencies(backend: str) -> bool:
    packages = ["httpx", "pydantic_settings", "dotenv"]
    if backend == "db_keyboard":
        packages.extend(["wxdb", "pyautogui", "pyperclip", "win32gui"])
    elif backend == "pyweixin":
        packages.append("pyweixin")
    else:
        packages.append("wcferry")

    missing: list[str] = []
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    if missing:
        _fail(f"缺少依赖: {', '.join(missing)}")
        _warn("运行: .venv\\Scripts\\pip install -r requirements.txt")
        return False
    _ok(f"Python 依赖已安装 ({backend})")
    return True


def _find_wechat_installations() -> tuple[list[Path], list[Path]]:
    candidates = [
        Path(r"C:\Program Files\Tencent\WeChat"),
        Path(r"C:\Program Files (x86)\Tencent\WeChat"),
        Path(r"C:\Program Files\Tencent\Weixin"),
        Path(r"C:\Program Files (x86)\Tencent\Weixin"),
        ROOT / "wechat39",
    ]
    wechat39: list[Path] = []
    weixin4: list[Path] = []
    for base in candidates:
        for exe_name, bucket in (("WeChat.exe", wechat39), ("Weixin.exe", weixin4)):
            exe = base / exe_name
            if exe.exists():
                bucket.append(exe)
    return wechat39, weixin4


def _is_valid_db_key(key: str) -> bool:
    import re

    value = key.strip().lower()
    if value.startswith("0x"):
        value = value[2:]
    value = re.sub(r"[^0-9a-f]", "", value)
    return len(value) == 64


def check_db_keyboard() -> bool:
    weixin_running = _is_process_running("Weixin")
    _, weixin4 = _find_wechat_installations()

    if weixin4:
        for exe in weixin4:
            _ok(f"找到新版 Weixin 4.x: {exe}")
    else:
        _fail("未找到 Weixin.exe，请先安装新版微信")
        return False

    if not weixin_running:
        _fail("Weixin 4.x 未运行，请先打开新版微信并用小号登录")
        return False
    _ok("Weixin 4.x 运行中")

    try:
        import win32gui

        hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "微信")
        if hwnd == 0:
            hwnd = win32gui.FindWindow("Qt51514QWindowIcon", "Weixin")
        if hwnd == 0:
            _fail("未找到微信窗口，请保持微信已登录")
            return False
        _ok("微信窗口已找到")
    except ImportError:
        _fail("缺少 pywin32，请运行 pip install -r requirements.txt")
        return False

    db_key = _read_env_value("WECHAT_DB_KEY", "")
    if not db_key:
        _fail("未配置 WECHAT_DB_KEY")
        _warn(
            "用 wx_key 提取 64 位十六进制密钥后写入 .env\n"
            "  下载: https://github.com/ycccccccy/wx_key/releases\n"
            "  注意: wx_key 安装路径不要包含中文"
        )
        return False
    if not _is_valid_db_key(db_key):
        _fail("WECHAT_DB_KEY 格式无效（需要 64 位十六进制）")
        return False
    _ok("WECHAT_DB_KEY 已配置")

    try:
        from app.wechat.db_client import build_wxdb, resolve_account
        from app.wechat.db_listener import verify_message_database

        account = resolve_account(db_key)
        _ok(f"已识别 wxid={account.wxid}，版本 {account.version}")
        table_count = verify_message_database(build_wxdb(account))
        _ok(f"消息数据库可读，会话表数={table_count}")
    except Exception as exc:
        _fail(f"数据库连接失败: {exc}")
        _warn("请确认密钥正确且微信已登录")
        return False

    _warn("发送回复时会模拟键盘操作，期间请勿操作鼠标键盘")
    return True


def check_wechat(backend: str) -> bool:
    if backend == "db_keyboard":
        return check_db_keyboard()

    wechat39, weixin4 = _find_wechat_installations()
    wechat_running = _is_process_running("WeChat")
    weixin_running = _is_process_running("Weixin")

    if backend == "pyweixin":
        if weixin4:
            for exe in weixin4:
                _ok(f"找到新版 Weixin 4.x: {exe}")
        else:
            _fail("未找到 Weixin.exe，请先安装新版微信")
            return False

        if weixin_running:
            _ok("Weixin 4.x 运行中")
            try:
                from pyweixin.WeChatTools import Tools

                info = Tools.about_weixin()
                _ok(f"已登录 wxid={info.get('wxid', '')}，版本 {info.get('版本', '')}")
            except Exception as exc:
                _warn(f"无法读取微信登录信息: {exc}")

            ui_script = ROOT / "scripts" / "check_weixin_ui.py"
            try:
                result = subprocess.run(
                    [sys.executable, str(ui_script)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode == 0:
                    _ok("微信 UI 无障碍已就绪")
                    return True
                for line in result.stdout.splitlines():
                    if line.strip():
                        print(f"  {line.strip()}")
            except OSError as exc:
                _warn(f"无法检查微信 UI: {exc}")
            return False

        _fail("Weixin 4.x 未运行，请先打开新版微信并用小号登录")
        return False

    if wechat39:
        for exe in wechat39:
            _ok(f"找到 PC 微信 3.9: {exe}")
    else:
        _fail("未找到 PC 微信 3.9.x (WeChat.exe)")
        print(f"\n  提示: {WECHAT39_HINT}")
        return False

    if weixin4:
        for exe in weixin4:
            _warn(f"检测到新版 Weixin 4.x: {exe}（与 WeChatFerry 不兼容）")

    if wechat_running:
        _ok("PC 微信 3.9 运行中")
        return True
    if weixin_running:
        _fail("当前运行的是 Weixin 4.x，请在 .env 设置 WECHAT_BACKEND=pyweixin")
        return False

    _fail("PC 微信 3.9 未运行，请先用小号登录")
    return False


def check_env_file() -> bool:
    if not ENV_FILE.exists():
        _fail(".env 不存在")
        _warn(f"复制配置: copy .env.example .env")
        return False

    content = ENV_FILE.read_text(encoding="utf-8")
    if "your_xai_api_key" in content or "XAI_API_KEY=" not in content:
        _fail("请在 .env 中填写有效的 XAI_API_KEY")
        return False

    key = ""
    for line in content.splitlines():
        if line.startswith("XAI_API_KEY="):
            key = line.split("=", 1)[1].strip()
            break

    if not key or key == "your_xai_api_key":
        _fail("XAI_API_KEY 未配置")
        _warn("在 https://console.x.ai/ 获取 API Key 后写入 .env")
        return False

    _ok(".env 已配置 XAI_API_KEY")
    backend = _read_env_value("WECHAT_BACKEND", "db_keyboard").lower()
    _ok(f"微信后端: {backend}")
    return True


def main() -> int:
    backend = _read_env_value("WECHAT_BACKEND", "db_keyboard").lower()
    if backend not in {"db_keyboard", "pyweixin", "wcferry"}:
        backend = "db_keyboard"

    print("=== grok-wechat 环境检查 ===\n")
    checks = [
        ("Python", check_python),
        ("平台", check_platform),
        ("依赖", lambda: check_dependencies(backend)),
        ("微信", lambda: check_wechat(backend)),
        ("配置", check_env_file),
    ]

    results: list[bool] = []
    for title, fn in checks:
        print(f"[{title}]")
        results.append(fn())
        print()

    if all(results):
        print("全部检查通过，可以运行: .venv\\Scripts\\python run.py")
        print("或双击: 启动机器人.bat")
        return 0

    print("部分检查未通过，请按上方提示修复后再启动。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())