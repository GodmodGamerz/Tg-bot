from aiogram import Router, F
from aiogram.types import Message, ReplyParameters, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from aiogram import Bot
import logging
from llm_agent import process_prompt, set_user_model, get_user_model
from openai import AsyncOpenAI
from config import Config

router = Router()
logger = logging.getLogger(__name__)

# Image client setup
image_client = AsyncOpenAI(
    api_key=Config.OPENAI_API_KEY,
    base_url=Config.OPENAI_BASE_URL or "https://api.openai.com/v1"
)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Hi! I'm AlienLM with real-time web search and image generation.\n\n"
        "Just chat normally or use /imagine &lt;prompt&gt;\n"
        "Type /model to change AI model",
        parse_mode="HTML"
    )

@router.message(Command("model"))
async def cmd_model(message: Message):
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Nemotron (Science/Math)", callback_data="set_model:nvidia/nemotron-3-super-120b-a12b")],
            [InlineKeyboardButton(text="🔵 GPT (Reasoning)", callback_data="set_model:openai/gpt-oss-120b")],
            [InlineKeyboardButton(text="🔴 DeepSeek (Fast Logic)", callback_data="set_model:deepseek-ai/deepseek-v4-pro")]
        ]
    )
    current = get_user_model(message.from_user.id)
    await message.answer(
        f"Current model: <b>{current}</b>\n\nChoose a new model:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )

@router.callback_query(F.data.startswith("set_model:"))
async def callback_set_model(callback):
    model = callback.data.split(":", 1)[1]
    set_user_model(callback.from_user.id, model)
    
    # Check if AVAILABLE_MODELS is in Config, otherwise just use the raw ID
    name_map = {v: k for k, v in getattr(Config, "AVAILABLE_MODELS", {}).items()}
    nice_name = name_map.get(model, model)
    
    await callback.message.edit_text(
        f"✅ Model changed to <b>{nice_name}</b>\n<code>{model}</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("imagine"))
async def cmd_imagine(message: Message, bot: Bot):
    prompt = message.text.replace("/imagine", "").strip()
    if not prompt:
        await message.answer("Usage: /imagine a cute cat astronaut")
        return

    # Send loading state with quote
    loading = await message.answer(
        text="⏳",
        reply_parameters=ReplyParameters(
            message_id=message.message_id,
            quote=prompt[:120]
        )
    )

    try:
        response = await image_client.images.generate(
            model=getattr(Config, 'IMAGE_MODEL', "dall-e-3"),
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1
        )
        image_url = response.data[0].url

        await bot.delete_message(loading.chat.id, loading.message_id)
        await message.answer_photo(
            photo=image_url,
            caption=f"🖼️ Generated\nPrompt: {prompt}",
            reply_to_message_id=message.message_id 
        )
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        await bot.delete_message(loading.chat.id, loading.message_id)
        await message.answer("❌ Image generation failed.", reply_to_message_id=message.message_id)

@router.message(F.text & ~F.text.startswith("/"))
async def handle_any_message(message: Message, bot: Bot):
    """Main chat flow: ⏳ -> Fetch Answer -> Chunk if needed -> Clean Reply"""
    loading = await message.answer(
        text="⏳",
        reply_parameters=ReplyParameters(
            message_id=message.message_id,
            quote=message.text[:120]
        )
    )

    try:
        # Get raw response formatted with AI's own HTML tags
        response_text = await process_prompt(
            user_id=message.from_user.id,
            prompt=message.text
        )
        
        # Telegram limit is 4096. We slice at 4000 just to be safe.
        MAX_LENGTH = 4000
        chunks = [response_text[i:i + MAX_LENGTH] for i in range(0, len(response_text), MAX_LENGTH)]
        
        # Delete the hourglass ⏳
        await bot.delete_message(loading.chat.id, loading.message_id)
        
        # Send text in sequential chunks
        for i, chunk in enumerate(chunks):
            if i == 0:
                # First chunk naturally replies to user's question
                await message.answer(
                    text=chunk,
                    reply_to_message_id=message.message_id,
                    parse_mode="HTML"
                )
            else:
                # Subsequent chunks are sent silently below it
                await message.answer(
                    text=chunk,
                    parse_mode="HTML"
                )

    except Exception as e:
        logger.error(f"LLM error: {e}")
        try:
            await bot.delete_message(loading.chat.id, loading.message_id)
        except:
            pass
            
        await message.answer(
            f"❌ Sorry, something went wrong. (Error: {str(e)[:50]})",
            reply_to_message_id=message.message_id
        )
