import os
import logging
import asyncio
from datetime import datetime
from io import BytesIO

from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

# Enable logging
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

# ---------- Flask App ----------
app = Flask(__name__)

# ---------- Telegram Application ----------
application = Application.builder().token(BOT_TOKEN).build()

# ---------- Handlers ----------
async def start(update: Update, context):
    """Send a professional welcome message with inline keyboard."""
    keyboard = [
        [
            InlineKeyboardButton("📄 Convert Text", callback_data="convert"),
            InlineKeyboardButton("ℹ️ How it Works", callback_data="how"),
        ],
        [
            InlineKeyboardButton("🔗 Support / Channel", url="https://t.me/yourchannel"),  # Replace with your channel
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
    """Send detailed help message."""
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
    """Capture user text, create a .txt file, and send it back as a document."""
    user_text = update.message.text
    if not user_text:
        return

    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"sbc24_note_{timestamp}.txt"

    # Write text to an in‑memory bytes buffer
    file_bytes = BytesIO()
    file_bytes.write(user_text.encode("utf-8"))
    file_bytes.seek(0)

    # Send the file as a document
    await update.message.reply_document(
        document=file_bytes,
        filename=filename,
        caption="Here's your text file! 📄",
    )

async def button_callback(update: Update, context):
    """Handle inline button presses."""
    query = update.callback_query
    await query.answer()  # Acknowledge the callback

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

# Register all handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
application.add_handler(CallbackQueryHandler(button_callback))

# ---------- Webhook Setup ----------
async def set_webhook():
    """Set the webhook URL for the bot."""
    webhook_url = f"{WEBHOOK_URL}/webhook"
    await application.bot.set_webhook(url=webhook_url)
    logger.info(f"Webhook set to {webhook_url}")

_webhook_set = False

@app.before_first_request
def setup_webhook():
    """Run the async webhook setup once before the first request."""
    global _webhook_set
    if not _webhook_set:
        try:
            asyncio.run(set_webhook())
            _webhook_set = True
        except Exception as e:
            logger.error(f"Failed to set webhook: {e}")

# ---------- Flask Webhook Endpoint ----------
@app.route("/webhook", methods=["POST"])
def webhook():
    """Receive incoming Telegram updates and process them."""
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

# ---------- Local Development ----------
if __name__ == "__main__":
    # Set webhook and run the Flask development server
    asyncio.run(set_webhook())
    app.run(host="0.0.0.0", port=PORT)
