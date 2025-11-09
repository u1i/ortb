"""Telegram handlers for messages and commands."""
from __future__ import annotations

import logging
import asyncio
from functools import wraps
from io import BytesIO

from telegram import Update, Voice, PhotoSize
from telegram.ext import ContextTypes
from telegram.constants import ParseMode
from datetime import datetime
from telegram import error as tg_error
from openai import OpenAI, APIError  # type: ignore

from .config import settings
from .constants import whitelist_key
from .redis_store import key_exists
from .session import Conversation
from .llm import chat as llm_chat

logger = logging.getLogger(__name__)


# ---------- Decorators ----------

def whitelist_required(func):  # type: ignore
    """Decorator to ensure user is whitelisted before proceeding."""

    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):  # type: ignore
        user = update.effective_user
        if user is None:
            return
        if not key_exists(whitelist_key(user.id)):
            await update.message.reply_text(f"Sorry, you are not authorised to use this bot. (user_id={user.id})")
            return
        return await func(update, context)

    return wrapper


# ---------- Command handlers ----------


@whitelist_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    user = update.effective_user
    if not user:
        return
    # new conversation id timestamp with seconds for uniqueness
    conv_id = datetime.now().strftime("%Y%m%d_%H%M%S")
    context.user_data["conv_id"] = conv_id
    conv = Conversation(user_id=user.id, conv_id=conv_id)
    greeting = settings.BOT_GREETING.replace("{{username}}", user.first_name)
    await update.message.reply_text(greeting)


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    await update.message.reply_text(
        "Send text, voice, or photo. Voice will be transcribed; images give a placeholder response."
    )


# ---------- Message handlers ----------


@whitelist_required
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    if not update.message or not update.message.text:
        return
    user = update.effective_user
    conv_id = context.user_data.get("conv_id", "default")
    conv = Conversation(user_id=user.id, conv_id=conv_id)
    conv.append("user", update.message.text)

    try:
        assistant_reply = await asyncio.to_thread(llm_chat, conv.messages)
    except APIError as exc:
        logger.error("LLM API error: %s", exc)
        assistant_reply = "Sorry, there was an error talking to the language model."

    conv.append("assistant", assistant_reply)

    await update.message.reply_text(assistant_reply)


@whitelist_required
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    if not update.message or not update.message.voice:
        return
    voice: Voice = update.message.voice
    file = await voice.get_file()
    file_bytes = await file.download_as_bytearray()

    # Transcribe with Whisper via OpenAI
    txt = "Could not transcribe."
    try:
        client = OpenAI(api_key=settings.OPENROUTER_API_KEY, base_url="https://openrouter.ai/api/v1")
        transcription = client.audio.transcriptions.create(file=BytesIO(file_bytes), model="openai/whisper-large-v3")
        txt = transcription.text  # type: ignore[attr-defined]
    except APIError as exc:
        logger.error("Whisper API error: %s", exc)
        txt = "(transcription failed)"

    # Reuse text handler
    update.message.text = txt  # type: ignore[attr-defined]
    await handle_text(update, context)


@whitelist_required
async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    if not update.message or not update.message.photo:
        return
    photo: PhotoSize = update.message.photo[-1]  # highest resolution
    file = await photo.get_file()

    # Build Telegram file URL that is publicly accessible via bot token
    # Telegram may return absolute URL or relative path.
    if file.file_path.startswith("http"):
        file_url = file.file_path
    else:
        file_url = f"https://api.telegram.org/file/bot{settings.TELEGRAM_BOT_TOKEN}/{file.file_path}"

    # Retrieve current conversation
    user = update.effective_user
    conv_id = context.user_data.get("conv_id", "default")
    conv = Conversation(user_id=user.id, conv_id=conv_id)

    # Build vision message
    vision_msg = {
        "role": "user",
        "content": [
            {"type": "text", "text": update.message.caption},
            {"type": "image_url", "image_url": {"url": file_url}},
        ],
    }

    messages = conv.messages + [vision_msg]

    try:
        assistant_reply = await asyncio.to_thread(llm_chat, messages)
    except APIError as exc:
        logger.error("LLM vision API error: %s", exc)
        assistant_reply = "Sorry, there was an error processing the image."

    conv.append("assistant", assistant_reply)
    await update.message.reply_text(assistant_reply)


# ---------- Error handler ----------


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:  # noqa: D401
    logger.error("Exception while handling an update:", exc_info=context.error)
    if isinstance(update, Update) and update.message:
        await update.message.reply_text("An internal error occurred.")
