"""
Wayhall Civic AI — Telegram Bot Example.

Connects Telegram users directly to the Wayhall Municipal RAG Engine.
Residents can ask bylaw, permit, or service request questions and receive
strictly grounded answers with verified PDF page citations.

Prerequisites:
    pip install python-telegram-bot

Usage:
    export TELEGRAM_BOT_TOKEN="your_bot_token_from_botfather"
    python -m mcp_server.examples.telegram_bot
"""

import os
import sys
from pathlib import Path

# Ensure backend root is in sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from dotenv import load_dotenv
load_dotenv(BACKEND_DIR / ".env")

try:
    from telegram import Update
    from telegram.ext import (
        ApplicationBuilder,
        CommandHandler,
        ContextTypes,
        MessageHandler,
        filters,
    )
except ImportError:
    print(
        "Error: 'python-telegram-bot' not installed. Run: pip install python-telegram-bot",
        file=sys.stderr,
    )
    sys.exit(1)

from app.core.rag.pipeline import run_rag_pipeline

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Greets the resident and explains what Cedarhaven topics are covered."""
    greeting = (
        "🏛️ *Wayhall Civic Assistant — Cedarhaven*\n\n"
        "Hello! I am your AI assistant for official Cedarhaven municipal information.\n\n"
        "You can ask me about:\n"
        "• 🔊 *Bylaws & Quiet Hours* (noise rules, parking bans, property standards)\n"
        "• 🔨 *Permits & Licences* (storage sheds, decks, business licences)\n"
        "• 🚯 *Service Requests* (311 response times, potholes, missed collection)\n\n"
        "Just send me your question directly!"
    )
    await update.message.reply_text(greeting, parse_mode="Markdown")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Processes resident questions through the RAG pipeline."""
    if not update.message or not update.message.text:
        return

    user_query = update.message.text.strip()
    await update.message.chat.send_action("typing")

    try:
        result = await run_rag_pipeline(user_question=user_query, history=[])
        reply = result.answer.strip()

        # Format verified citations if available
        if result.citations:
            reply += "\n\n📚 *Verified Sources:*"
            for cit in result.citations[:3]:
                sec = f" § {cit.section}" if cit.section else ""
                reply += f"\n• `{cit.source}` (Page {cit.page}){sec}"

        # Mention gap if any part is uncovered
        if result.unsupported_parts:
            reply += (
                f"\n\n⚠️ *Notice:* Information on {', '.join(result.unsupported_parts)} "
                "is not covered in official municipal bylaws."
            )

        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as exc:
        await update.message.reply_text(
            f"Sorry, an error occurred while checking municipal records: {str(exc)}"
        )


def main():
    if not BOT_TOKEN:
        print(
            "ERROR: TELEGRAM_BOT_TOKEN environment variable not set.\n"
            "Create a bot with @BotFather on Telegram and set:\n"
            "  export TELEGRAM_BOT_TOKEN='your-token-here'\n",
            file=sys.stderr,
        )
        sys.exit(1)

    print("🏛️ Wayhall Telegram Bot starting polling...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.run_polling()


if __name__ == "__main__":
    main()
