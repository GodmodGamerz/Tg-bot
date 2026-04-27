import asyncio
import logging
from aiogram import Bot, Dispatcher
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
    This is where the bot actually starts.
    1. Loads your environment variables
    2. Creates the Telegram Bot instance
    3. Registers all handlers (commands + normal messages)
    4. Starts polling (listening for messages)
    """
    
    # Validate that all required API keys are present
    Config.validate()
    
    # Create the bot with your Telegram token
    bot = Bot(token=Config.TELEGRAM_TOKEN, parse_mode="HTML")
    
    # Create the dispatcher (handles incoming messages)
    dp = Dispatcher()
    
    # Include all our handlers (start, imagine, normal chat, etc.)
    dp.include_router(router)
    
    # Optional: Clear any old pending updates when the bot starts
    await bot.delete_webhook(drop_pending_updates=True)
    
    print("🤖 Telegram AI Bot is now RUNNING – polling for messages...")
    logger.info("Bot started successfully!")
    
    # Start the bot
    await dp.start_polling(bot)

# ==========================
# RUN THE BOT
# ==========================
if __name__ == "__main__":
    asyncio.run(main())
