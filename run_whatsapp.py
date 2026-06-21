import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings
from app.whatsapp.preflight import validate_whatsapp_startup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)


def main() -> None:
    settings = get_settings()
    validate_whatsapp_startup(settings)
    from app.whatsapp.bot import run_whatsapp_bot

    run_whatsapp_bot(settings)


if __name__ == "__main__":
    main()