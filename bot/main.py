import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties

from .config import config
from .services.database import db
from .handlers import start, menu, free_calc, premium, referrals, help

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    
    dp = Dispatcher()
    
    # Register routers
    dp.include_routers(
        start.router,
        menu.router,
        free_calc.router,
        premium.router,
        referrals.router,
        help.router
    )
    
    # Initialize database
    await db.init_db()
    
    # Start polling
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())