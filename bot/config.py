from pydantic_settings import BaseSettings
from pydantic import Field

class Config(BaseSettings):
    BOT_TOKEN: str = Field(default="")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///data/bot.db")

    # LLM Settings
    LLM_API_KEY: str = Field(default="")
    LLM_API_URL: str = Field(default="https://api.groq.com/openai/v1/chat/completions")
    LLM_MODEL: str = Field(default="llama-3.3-70b-versatile")

    # Payment Settings
    PAYMENT_PROVIDER_TOKEN: str = Field(default="")
    YOOKASSA_SHOP_ID: str = Field(default="")
    YOOKASSA_SECRET_KEY: str = Field(default="")
    YOOKASSA_RETURN_URL: str = Field(default="https://t.me/kod_sudby_bot")

    # Freemium Settings
    FREE_CALC_LIMIT: int = Field(default=3)
    REFERRAL_BONUS_THRESHOLD: int = Field(default=3)

    # PDF Settings
    PDF_FONT_PATH: str = Field(default="data/templates/font.ttf")

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

config = Config()
