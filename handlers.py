import os
import re
import base64
import logging
from aiogram import Router, F, Bot
from aiogram.types import Message, ReplyParameters, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from openai import AsyncOpenAI
from llm_agent import process_prompt, set_user_model, get_user_model, generate_image
from config import Config

router = Router()
logger = logging.getLogger(__name__)

# System info
CREATOR = "@FirgunDarchi"

@router.message(Command("start"))
async def cmd_start(message: Message):
    """Start command with updated capabilities menu"""
    await message.answer(
        f"👋 Hi! I'm <b>AlienLM</b>, powered by the fastest NVIDIA NIM clusters.\n\n"
        f"I can process your text, analyze complex textbook diagrams from your photos, "
        f"and generate stunning images.\n\n"
        "Just chat normally, use /imagine &lt;prompt&gt;, or upload a photo.\n"
        "Type /model to change AI model",
        parse_mode="HTML"
    )

@router.message(Command("model"))
async def cmd_model(message: Message):
    """Inline menu to select between distinct heavyweights"""
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 Nemotron (Science)", callback_data="set_model:nvidia/nemotron-3-super-120b-a12b")],
            [InlineKeyboardButton(text="🔵 GPT (Logic)", callback_data="set_model:openai/gpt-oss-120b")],
            [InlineKeyboardButton(text="⚡ DeepSeek (Flash)", callback_data="set_model:deepseek-ai/deepseek-v4-flash")],
            [InlineKeyboardButton(text="👁️ Vision (Llama 3.2)", callback_data=f"set_model:{getattr(Config, 'VISION_MODEL', 'nvidia/llama-3.2-11b-vision-instruct')}")]
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
    
    name_map = {v: k for k, v in getattr(Config, "AVAILABLE_MODELS", {}).items()}
    nice_name = name_map.get(model, model)
    
    await callback.message.edit_text(
        f"✅ Model changed to <b>{nice_name}</b>\n<code>{model}</code>",
        parse_mode="HTML"
    )
    await callback.answer()

@router.message(Command("imagine"))
async def cmd_imagine(message: Message, bot: Bot):
    """NIM Image Generation Handler"""
    prompt = message.text.replace("/imagine", "").strip()
    if not prompt:
        await message.answer("Usage: /imagine a cute cat astronaut")
        return

    loading = await message.answer(
        text="🎨 ⏳ <b>Generating your masterpiece...</b>",
        reply_parameters=ReplyParameters(message_id=message.message_id, quote=prompt[:120]),
        parse_mode="HTML"
    )

    try:
        # Call NIM generation logic
        image_url = await generate_image(prompt)

        await bot.delete_message(loading.chat.id, loading.message_id)
        await message.answer_photo(
            photo=image_url,
            caption=f"🖼️ <b>Generated Piece</b>\nPrompt: <i>{prompt}</i>\nCreated by AlienLM",
            reply_to_message_id=message.message_id,
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Image gen error: {e}")
        await bot.delete_message(loading.chat.id, loading.message_id)
        await message.answer(
            f"❌ Image generation failed.\n(Error: {str(e)[:50]})", 
            reply_to_message_id=message.message_id
        )

def process_safe_chunks(response_text: str) -> list:
    """Helper function to escape math symbols and chunk text cleanly by paragraphs."""
    # 1. Regex Tag Protector: Identifies approved HTML tags
    allowed_tags = re.compile(r'(</?(?:b|i|u|s|code|pre|blockquote)>)')
    parts = allowed_tags.split(response_text)
    
    # Escape dangerous math symbols outside of HTML tags
    for idx in range(0, len(parts), 2):
        parts[idx] = parts[idx].replace('<', '&lt;').replace('>', '&gt;')
        
    safe_response = "".join(parts)

    # 2. Smart Chunker: Split by newlines so tags/words aren't cut in half
    paragraphs = safe_response.split('\n')
    chunks = []
    current_chunk = ""
    
    for p in paragraphs:
        # Safe limit is 3900 to stay well under Telegram's 4096 limit
        if len(current_chunk) + len(p) + 1 > 3900:
            chunks.append(current_chunk.strip())
            current_chunk = p + "\n"
        else:
            current_chunk += p + "\n"
    
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
        
    return chunks

@router.message(F.photo)
async def handle_photo(message: Message, bot: Bot):
    """The 'Eyes' of the bot: detects photos, encodes to Base64, and calls Vision agent."""
    loading = await message.answer(
        text="📸 ⏳ <b>Analyzing image...</b>",
        reply_parameters=ReplyParameters(message_id=message.message_id),
        parse_mode="HTML"
    )

    try:
        # Get highest resolution version of photo
        photo_info = message.photo[-1]
        file_info = await bot.get_file(photo_info.file_id)
        
        # Download photo locally
        file_path = f"{file_info.file_id}.jpg"
        await bot.download_file(file_info.file_path, file_path)
        
        # Convert to Base64 encoded string
        with open(file_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')
        
        # Safe cleanup of the downloaded file
        try:
            os.remove(file_path)
        except Exception:
            pass

        # Call the agent
        response_text = await process_prompt(
            user_id=message.from_user.id,
            prompt=message.caption or "Analyze this image.", 
            image_data=base64_image
        )
        
        # Format and chunk safely
        chunks = process_safe_chunks(response_text)
        
        await bot.delete_message(loading.chat.id, loading.message_id)
        
        for i, chunk in enumerate(chunks):
            reply_id = message.message_id if i == 0 else None
            
            try:
                await message.answer(
                    text=chunk,
                    reply_to_message_id=reply_id,
                    parse_mode="HTML"
                )
            except Exception as parse_error:
                if "parse" in str(parse_error).lower() or "bad request" in str(parse_error).lower():
                    logger.warning(f"Vision HTML Parse Error. Sending raw text.")
                    await message.answer(
                        text=f"⚠️ <i>[Formatting Error - Showing Raw Text]</i>\n\n{chunk}",
                        reply_to_message_id=reply_id,
                        parse_mode=None
                    )
                else:
                    raise parse_error

    except Exception as e:
        logger.error(f"Vision error: {e}")
        try:
            await bot.delete_message(loading.chat.id, loading.message_id)
        except:
            pass
            
        await message.answer(
            f"❌ Sorry, image analysis failed.\n(Error: {str(e)[:50]})",
            reply_to_message_id=message.message_id
        )

@router.message(F.text & ~F.text.startswith("/"))
async def handle_any_message(message: Message, bot: Bot):
    """Standard chat flow using safe chunking and math escaping"""
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
        
        # Format and chunk safely using our helper function
        chunks = process_safe_chunks(response_text)
        
        await bot.delete_message(loading.chat.id, loading.message_id)
        
        for i, chunk in enumerate(chunks):
            reply_id = message.message_id if i == 0 else None
            
            try:
                await message.answer(
                    text=chunk,
                    reply_to_message_id=reply_id,
                    parse_mode="HTML"
                )
            except Exception as parse_error:
                if "parse" in str(parse_error).lower() or "bad request" in str(parse_error).lower():
                    logger.warning(f"HTML Parse Error caught. Sending raw text.")
                    await message.answer(
                        text=f"⚠️ <i>[Formatting Error - Showing Raw Text]</i>\n\n{chunk}",
                        reply_to_message_id=reply_id,
                        parse_mode=None
                    )
                else:
                    raise parse_error

    except Exception as e:
        logger.error(f"LLM error: {e}")
        try:
            await bot.delete_message(loading.chat.id, loading.message_id)
        except:
            pass
            
        await message.answer(
            f"❌ Sorry, something went wrong.\n(Error: {str(e)[:50]})",
            reply_to_message_id=message.message_id
        )
