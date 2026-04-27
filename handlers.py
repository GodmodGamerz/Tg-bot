from aiogram import Router, F
from aiogram.types import Message, ReplyParameters
from aiogram.filters import Command
from aiogram import Bot
import logging
from llm_agent import process_prompt
from openai import AsyncOpenAI
from config import Config

router = Router()
logger = logging.getLogger(__name__)
image_client = AsyncOpenAI(api_key=Config.OPENAI_API_KEY, base_url=Config.OPENAI_BASE_URL or "https://api.openai.com/v1")

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("👋 Hi! I'm an AI bot with real-time web search and image generation.\n\nJust send me any question or use /imagine <prompt>")

@router.message(Command("imagine"))
async def cmd_imagine(message: Message, bot: Bot):
    prompt = message.text.replace("/imagine", "").strip()
    if not prompt:
        await message.answer("Usage: /imagine a cute cat astronaut")
        return

    # ⏳ loading with quote
    loading = await message.answer(
        text="⏳",
        reply_parameters=ReplyParameters(
            message_id=message.message_id,
            quote=prompt[:120]  # Telegram quote preview
        )
    )

    try:
        response = await image_client.images.generate(
            model=Config.IMAGE_MODEL,
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url

        # Delete loading and send image (edit to media is complex; cleanest UX)
        await bot.delete_message(loading.chat.id, loading.message_id)
        await message.answer_photo(
            photo=image_url,
            caption=f"🖼️ Generated with {Config.IMAGE_MODEL}\nPrompt: {prompt}",
            reply_to_message_id=message.message_id
        )
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        await bot.edit_message_text(
            chat_id=loading.chat.id,
            message_id=loading.message_id,
            text=f"❌ Image generation failed: {str(e)[:200]}"
        )

@router.message(F.text & \~F.text.startswith("/"))
async def handle_any_message(message: Message, bot: Bot):
    """Main chat flow: immediate ⏳ → LLM + tools → edit message"""
    loading = await message.answer(
        text="⏳",
        reply_parameters=ReplyParameters(
            message_id=message.message_id,
            quote=message.text[:120]
        )
    )

    try:
        response_text = await process_prompt(
            user_id=message.from_user.id,
            prompt=message.text
        )
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading.message_id,
            text=response_text
        )
    except Exception as e:
        logger.error(f"LLM error: {e}")
        await bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=loading.message_id,
            text=f"❌ Sorry, something went wrong: {str(e)[:150]}"
        )
