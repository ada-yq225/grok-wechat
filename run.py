import logging

from app.config import get_settings
from app.personal.bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def main() -> None:
    settings = get_settings()
    run_bot(settings)


if __name__ == "__main__":
    main()