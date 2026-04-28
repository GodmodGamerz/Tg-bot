import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from config import Config
from handlers import router

# ==========================
# LOGGING SETUP
# ==========================
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# ==========================
# MAIN BOT STARTUP
# ==========================
async def main():
    """
    Bot startup function.
    """
    # Validate API keys
    Config.validate()
    
    # Create bot with new aiogram 3.7+ style
    bot = Bot(
        token=Config.TELEGRAM_TOKEN,
        default=DefaultBotProperties(parse_mode="HTML")
    )
    
    # Dispatcher
    dp = Dispatcher()
    
    # Register handlers
    dp.include_router(router)
    
    # Clear pending updates
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🤖 Telegram AI Bot is now RUNNING – polling for messages...")
    logger.info("Bot started successfully!")
    
    # Start polling
    await dp.start_polling(bot)

# ==========================
# RUN THE BOT
# ==========================
if __name__ == "__main__":
    asyncio.run(main())
