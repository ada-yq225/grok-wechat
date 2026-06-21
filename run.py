import logging

from app.config import get_settings
from app.preflight import validate_startup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def main() -> None:
    settings = get_settings()
    validate_startup(settings)
    backend = settings.wechat_backend.strip().lower()
    if backend == "db_keyboard":
        from app.personal.bot_db_keyboard import run_db_keyboard_bot

        run_db_keyboard_bot(settings)
    elif backend == "pyweixin":
        from app.personal.bot_weixin import run_weixin_bot

        run_weixin_bot(settings)
    elif backend == "wcferry":
        from app.personal.bot import run_bot

        run_bot(settings)
    else:
        raise SystemExit(
            f"未知的 WECHAT_BACKEND={settings.wechat_backend}，"
            "请使用 db_keyboard、pyweixin 或 wcferry"
        )


if __name__ == "__main__":
    main()