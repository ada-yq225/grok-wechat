import logging

import httpx

from app.config import Settings

logger = logging.getLogger(__name__)


class GrokClient:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client = httpx.Client(
            base_url=settings.xai_base_url.rstrip("/"),
            headers={
                "Authorization": f"Bearer {settings.xai_api_key}",
                "Content-Type": "application/json",
            },
            timeout=httpx.Timeout(120.0, connect=10.0),
        )

    def chat(self, history: list[dict[str, str]], user_message: str) -> str:
        messages = [
            {"role": "system", "content": self._settings.system_prompt},
            *history,
            {"role": "user", "content": user_message},
        ]

        payload = {
            "model": self._settings.grok_model,
            "messages": messages,
            "temperature": 0.7,
        }

        try:
            response = self._client.post("/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            content = data["choices"][0]["message"]["content"]
            if not content:
                return "抱歉，我这次没有生成有效回复，请再试一次。"
            return content.strip()
        except httpx.HTTPStatusError as exc:
            detail = exc.response.text[:300]
            logger.error("Grok API HTTP error: %s %s", exc.response.status_code, detail)
            return f"Grok 服务暂时不可用（HTTP {exc.response.status_code}），请稍后再试。"
        except Exception:
            logger.exception("Grok API request failed")
            return "调用 Grok 时发生错误，请稍后再试。"

    def close(self) -> None:
        self._client.close()