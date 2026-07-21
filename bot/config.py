from pydantic_settings import BaseSettings
from pydantic import Field

class Config(BaseSettings):
    BOT_TOKEN: str = Field(..., description="Telegram Bot Token")
    DATABASE_URL: str = Field(default="sqlite+aiosqlite:///data/bot.db")
    
    # LLM Settings
    LLM_API_KEY: str = Field(default="")
    LLM_API_URL: str = Field(default="https://api.groq.com/openai/v1/chat/completions")
    LLM_MODEL: str = Field(default="llama-3.1-70b-versatile")
    
    # Payment Settings
    PAYMENT_PROVIDER_TOKEN: str = Field(default="")
    YOOKASSA_SHOP_ID: str = Field(default="")
    YOOKASSA_SECRET: str = Field(default="")
    
    # Freemium Settings
    FREE_CALC_LIMIT: int = Field(default=3)
    REFERRAL_BONUS_THRESHOLD: int = Field(default=3)
    
    # PDF Settings
    PDF_FONT_PATH: str = Field(default="data/templates/font.ttf")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

config = Config()
