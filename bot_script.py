import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv
from threading import Thread

# Load environment variables
load_dotenv()
BOT_API_KEY = os.getenv('TELEGRAM_API_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL')
TARGET_USERNAME = os.getenv('TARGET_USERNAME')

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Initialize bot
application = ApplicationBuilder().token(BOT_API_KEY).build()

# /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Received /start command")
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot. To request a form, say /form?")

# /form command handler to open the Web App
async def form_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Received /form command")
    keyboard = [[InlineKeyboardButton("Open Form", web_app=WebAppInfo(WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click below to open the form:", reply_markup=reply_markup)

# Handler for data sent from the Web App
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        logging.info("Received data from Web App")
        web_app_data = update.message.web_app_data.data
        logging.debug(f"Web App data received: {web_app_data}")
        
        data = eval(web_app_data)  # Parse the string data into a dict (use `json.loads` if using JSON)
        text = data.get("text")

        if not text:
            logging.error("No text received in Web App data")
            return
        
        # Fetch the chat ID for the target username
        user = await application.bot.get_chat(username=TARGET_USERNAME)
        logging.debug(f"Found target chat ID: {user.id}")

        # Send message to target user
        await application.bot.send_message(chat_id=user.id, text=f"Received from form: {text}")
        logging.info("Message sent successfully to target user")

    except Exception as e:
        logging.error(f"Error processing Web App data: {e}")

# Register command handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('form', form_command))
application.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, web_app_data_handler))

# Start the bot
if __name__ == '__main__':
    logging.info("Starting Telegram bot")
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
