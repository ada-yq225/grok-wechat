"""WhatsApp 机器人启动前检查。"""

from __future__ import annotations

from app.config import Settings


def validate_whatsapp_startup(settings: Settings) -> None:
    if not settings.xai_api_key or settings.xai_api_key == "your_xai_api_key":
        raise SystemExit(
            "请在 .env 中配置 XAI_API_KEY（https://console.x.ai/）"
        )

    try:
        import neonize  # noqa: F401
    except ImportError as exc:
        raise SystemExit(
            "未安装 neonize。请运行: .venv\\Scripts\\pip install neonize"
        ) from exc