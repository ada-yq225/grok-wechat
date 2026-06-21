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

    # db_keyboard = Weixin 4.x 数据库监听 + 键盘发消息（推荐）
    # pyweixin = Weixin 4.x UI 自动化；wcferry = 旧版 PC 微信 3.9
    wechat_backend: str = "db_keyboard"

    # db_keyboard：64 位十六进制数据库密钥（wx_key 工具提取）
    wechat_db_key: str = ""
    db_poll_interval_sec: float = 1.0

    # WeChatFerry（连接本地或远程 Windows 微信客户端）
    wcf_host: str | None = None
    wcf_port: int = 10086

    # wcferry 模式：留空=所有好友；填写 wxid 逗号分隔
    allowed_wxids: str = ""
    # pyweixin 模式：留空=所有好友；填写好友备注/昵称逗号分隔
    allowed_friends: str = ""
    # 是否响应群聊（仅在被 @ 时回复）
    reply_in_group: bool = False

    # WhatsApp（run_whatsapp.py，后台运行，不依赖 PC 微信）
    whatsapp_session_name: str = "grok-whatsapp"
    # 留空=所有联系人；填写手机号逗号分隔，如 8613800138000,15551234567
    allowed_whatsapp_numbers: str = ""
    whatsapp_reply_in_group: bool = False
    # 是否响应「发给自己/Message yourself」的消息
    whatsapp_reply_to_self: bool = True

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

    def allowed_friends_set(self) -> set[str] | None:
        if not self.allowed_friends.strip():
            return None
        return {
            item.strip() for item in self.allowed_friends.split(",") if item.strip()
        }

    def allowed_whatsapp_set(self) -> set[str] | None:
        if not self.allowed_whatsapp_numbers.strip():
            return None
        return {
            item.strip()
            for item in self.allowed_whatsapp_numbers.split(",")
            if item.strip()
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()