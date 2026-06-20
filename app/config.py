from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    xai_api_key: str
    xai_base_url: str = "https://api.x.ai/v1"
    grok_model: str = "grok-3"

    # WeChatFerry（连接本地或远程 Windows 微信客户端）
    wcf_host: str | None = None
    wcf_port: int = 10086

    # 留空 = 所有好友都可聊；填写 wxid，逗号分隔 = 白名单
    allowed_wxids: str = ""
    # 是否响应群聊（仅在被 @ 时回复）
    reply_in_group: bool = False

    max_history_turns: int = 10
    system_prompt: str = (
        "你是一个友好、简洁的中文 AI 助手，由 Grok 驱动。回答要准确、有条理。"
    )

    @field_validator("wcf_host", mode="before")
    @classmethod
    def empty_host_to_none(cls, value: object) -> str | None:
        if value is None or value == "":
            return None
        return str(value)

    def allowed_set(self) -> set[str] | None:
        if not self.allowed_wxids.strip():
            return None
        return {item.strip() for item in self.allowed_wxids.split(",") if item.strip()}


@lru_cache
def get_settings() -> Settings:
    return Settings()