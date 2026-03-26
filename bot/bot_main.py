"""
bot_main.py – Telegram bot entry point.

Initialises the Application, registers handlers, and starts polling.
"""

from __future__ import annotations

from telegram.ext import Application, CallbackQueryHandler, MessageHandler, filters

from app.utils.helpers import get_env, setup_logging
from bot.handlers import build_conversation_handler, download_improved, handle_question

logger = setup_logging("drcode.bot_main")


def main() -> None:
    """Build the Telegram bot application and run polling."""
    token = get_env("TELEGRAM_BOT_TOKEN", "")

    if not token or token == "your-telegram-bot-token-here":
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set! "
            "Please add it to your .env file. "
            "Get a token from @BotFather on Telegram."
        )
        raise SystemExit(1)

    logger.info("Starting DRCode Telegram Bot …")

    # Build application
    application = Application.builder().token(token).build()

    # Register conversation handler
    conv_handler = build_conversation_handler()
    application.add_handler(conv_handler)

    # Register callback for download button
    application.add_handler(
        CallbackQueryHandler(download_improved, pattern="^download_improved$")
    )

    # Register Q&A text handler (only catches text outside the ConversationHandler)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_question)
    )

    # Start polling
    logger.info("Bot is ready! Listening for messages …")
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
