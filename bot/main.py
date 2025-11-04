"""Entry point for the telegram bot."""
from __future__ import annotations

import logging

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
)

from .config import settings
from .handlers import (
    start,
    help_cmd,
    handle_text,
    handle_voice,
    handle_photo,
    error_handler,
)

logging.basicConfig(level=logging.INFO)
# Silence noisy httpx INFO logs (only warnings/errors)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    if not settings.TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN not set in environment")

    app = (
        ApplicationBuilder()
        .token(settings.TELEGRAM_BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_text))
    # app.add_handler(MessageHandler(filters.VOICE, handle_voice))  # DISABLED: WIP - needs fixing
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))

    # Error
    app.add_error_handler(error_handler)

    logger.info("Starting bot as @%s", settings.BOT_NAME)
    # Run the bot until interrupted
    app.run_polling()


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, SystemExit):
        print("Bot stopped.")
