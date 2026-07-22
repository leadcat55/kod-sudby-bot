import os


class Config:
    def __init__(self):
        # Telegram
        self.BOT_TOKEN = (
            os.environ.get("BOT_TOKEN", "").strip()
            or os.environ.get("telegram_token", "").strip()
            or os.environ.get("TELEGRAM_TOKEN", "").strip()
        )

        # Database
        self.DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///data/bot.db")

        # LLM
        self.LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
        self.LLM_API_URL = os.environ.get("LLM_API_URL", "https://api.groq.com/openai/v1/chat/completions")
        self.LLM_MODEL = os.environ.get("LLM_MODEL", "llama-3.3-70b-versatile")

        # Payments
        self.PAYMENT_PROVIDER_TOKEN = os.environ.get("PAYMENT_PROVIDER_TOKEN", "")
        self.YOOKASSA_SHOP_ID = os.environ.get("YOOKASSA_SHOP_ID", "")
        self.YOOKASSA_SECRET_KEY = os.environ.get("YOOKASSA_SECRET_KEY", "")
        self.YOOKASSA_RETURN_URL = os.environ.get("YOOKASSA_RETURN_URL", "https://t.me/kod_sudby_bot")

        # Freemium
        self.FREE_CALC_LIMIT = int(os.environ.get("FREE_CALC_LIMIT", "3"))
        self.REFERRAL_BONUS_THRESHOLD = int(os.environ.get("REFERRAL_BONUS_THRESHOLD", "3"))

        # PDF
        self.PDF_FONT_PATH = os.environ.get("PDF_FONT_PATH", "data/templates/font.ttf")


config = Config()
