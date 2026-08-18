import os
import logging
import asyncio
from datetime import datetime
from io import BytesIO

from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# ---------- Logging ----------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---------- Environment Variables ----------
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN environment variable not set")

WEBHOOK_URL = os.environ.get("WEBHOOK_URL")
if not WEBHOOK_URL:
    raise ValueError("WEBHOOK_URL environment variable not set")

PORT = int(os.environ.get("PORT", 5000))

# ---------- Flask & Telegram App ----------
app = Flask(__name__)
application = Application.builder().token(BOT_TOKEN).build()

# ---------- Handlers (same as before) ----------
async def start(update: Update, context):
    keyboard = [
        [
            InlineKeyboardButton("📄 Convert Text", callback_data="convert"),
            InlineKeyboardButton("ℹ️ How it Works", callback_data="how"),
        ],
        [
            InlineKeyboardButton("🔗 Support / Channel", url="https://t.me/yourchannel"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome_text = (
        "👋 Welcome to SBC24Texttofilebot!\n\n"
        "This bot instantly converts any text message, code snippet, or notes you send here "
        "into a downloadable .txt file format.\n\n"
        "⚡️ How to use:\n"
        "1. Simply type or paste any text directly into this chat.\n"
        "2. Receive your compiled text document instantly!\n\n"
        "Use the interactive buttons below to navigate or read the guide."
    )
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def help_command(update: Update, context):
    help_text = (
        "📄 **How to Convert Text:**\n"
        "Just send me any text message, and I'll convert it to a .txt file for you.\n\n"
        "📂 **File Naming:**\n"
        "Files are named with a timestamp: `sbc24_note_YYYYMMDD_HHMMSS.txt`\n\n"
        "🔒 **Privacy:**\n"
        "Your text is processed and the file is sent back to you; I do not store any data.\n\n"
        "For support, contact @yourhandle."
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")

async def handle_text(update: Update, context):
    user_text = update.message.text
    if not user_text:
        return
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sbc24_note_{timestamp}.txt"
    file_bytes = BytesIO()
    file_bytes.write(user_text.encode("utf-8"))
    file_bytes.seek(0)
    await update.message.reply_document(
        document=file_bytes,
        filename=filename,
        caption="Here's your text file! 📄",
    )

async def button_callback(update: Update, context):
    query = update.callback_query
    await query.answer()
    data = query.data
    if data == "convert":
        await query.edit_message_text(
            text="📝 Please send me any text, code, or note, and I'll convert it to a .txt file for you."
        )
    elif data == "how":
        help_text = (
            "📄 **How to Convert Text:**\n"
            "Just send me any text message, and I'll convert it to a .txt file for you.\n\n"
            "📂 **File Naming:**\n"
            "Files are named with a timestamp: `sbc24_note_YYYYMMDD_HHMMSS.txt`\n\n"
            "🔒 **Privacy:**\n"
            "Your text is processed and the file is sent back to you; I do not store any data.\n\n"
            "For support, contact @yourhandle."
        )
        await query.edit_message_text(text=help_text, parse_mode="Markdown")

# Register handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(button_callback))

# ---------- Webhook Setup (runs once at startup) ----------
def set_webhook_sync():
    """Synchronous wrapper to set the webhook."""
    try:
        asyncio.run(application.bot.set_webhook(url=f"{WEBHOOK_URL}/webhook"))
        logger.info(f"Webhook set to {WEBHOOK_URL}/webhook")
    except Exception as e:
        logger.error(f"Failed to set webhook: {e}")

# Run this when the module is imported (i.e., when the worker starts)
set_webhook_sync()

# ---------- Flask Webhook Endpoint ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    json_data = request.get_json(force=True)
    if not json_data:
        return jsonify({"status": "error", "message": "No data"}), 400
    try:
        update = Update.de_json(json_data, application.bot)
        asyncio.run(application.process_update(update))
    except Exception as e:
        logger.error(f"Error processing update: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500
    return jsonify({"status": "ok"}), 200

# ---------- Main Entry Point ----------
if __name__ == "__main__":
    # When run with `python bot.py`, start the Flask dev server.
    # The webhook is already set above, so no need to set again.
    app.run(host="0.0.0.0", port=PORT)
