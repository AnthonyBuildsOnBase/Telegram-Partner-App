import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from threading import Thread

# Load environment variables from .env file
load_dotenv()
BOT_API_KEY = os.getenv('TELEGRAM_API_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL')
TARGET_USERNAME = os.getenv('TARGET_USERNAME')  # Add this variable in your .env file

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Initialize Flask app
app = Flask(__name__)

# Initialize Telegram bot application
application = ApplicationBuilder().token(BOT_API_KEY).build()

# Define the /start command handler
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot. To request a form, say /form?")

# Define the /form command handler with inline keyboard button to open web app
async def form_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Open Form", web_app=WebAppInfo(WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click below to open the form:", reply_markup=reply_markup)

# Handler for receiving data from the Web App via the form
@app.route('/api/submit', methods=['POST'])
async def receive_data():
    data = request.get_json()
    text = data.get("text")
    if not text:
        return jsonify({"status": "error", "message": "No text provided"}), 400
    
    try:
        # Fetch the chat ID for the target username
        user = await application.bot.get_chat(username=TARGET_USERNAME)
        await application.bot.send_message(chat_id=user.id, text=f"Received from form: {text}")
        return jsonify({"status": "success", "message": "Message sent"})
    except Exception as e:
        logging.error(f"Error sending message to target username: {e}")
        return jsonify({"status": "error", "message": "Failed to send message"}), 500

# Register command handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('form', form_command))

# Run Flask server in a separate thread to avoid blocking the bot polling
def run_flask():
    app.run(port=5000)

if __name__ == '__main__':
    flask_thread = Thread(target=run_flask)
    flask_thread.start()
    application.run_polling()
