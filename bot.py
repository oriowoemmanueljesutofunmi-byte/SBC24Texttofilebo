import os
import logging
from datetime import datetime
from io import BytesIO

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set")

app = Application.builder().token(BOT_TOKEN).build()

async def start(update, context):
    keyboard = [
        [InlineKeyboardButton("📄 Convert Text", callback_data="convert")],
        [InlineKeyboardButton("ℹ️ How it Works", callback_data="how")],
        [InlineKeyboardButton("🔗 Support", url="https://t.me/yourchannel")]
    ]
    await update.message.reply_text(
        "👋 Welcome!\nSend me any text and I'll return a .txt file.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def help_command(update, context):
    await update.message.reply_text("Send any text and I'll convert it to a .txt file.")

async def handle_text(update, context):
    text = update.message.text
    if not text:
        return
    filename = f"sbc24_note_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    file_bytes = BytesIO(text.encode("utf-8"))
    file_bytes.seek(0)
    await update.message.reply_document(
        document=file_bytes,
        filename=filename,
        caption="Here's your file!"
    )

async def button_callback(update, context):
    query = update.callback_query
    await query.answer()
    if query.data == "convert":
        await query.edit_message_text("Send me any text and I'll convert it.")
    elif query.data == "how":
        await query.edit_message_text("I convert text to a .txt file.")

app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
app.add_handler(CallbackQueryHandler(button_callback))

if __name__ == "__main__":
    logger.info("Bot started with long polling.")
    app.run_polling()
