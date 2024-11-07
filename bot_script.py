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
WEB_APP_URL = os.getenv('WEB_APP_URL')  # Add this variable to your .env file

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
    try:
        await context.bot.send_message(chat_id=update.effective_chat.id, text="Hello! I'm your bot. To request a form, say /form?")
    except Exception as e:
        logging.error(f"Error sending message: {e}")

# Define the /form command handler with inline keyboard button to open web app
async def form_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        # Inline keyboard with a web_app type button to open the Mini App inline within Telegram
        keyboard = [[InlineKeyboardButton("Open Form", web_app=WebAppInfo(WEB_APP_URL))]]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Click below to open the form:", reply_markup=reply_markup)
    except Exception as e:
        logging.error(f"Error sending form link: {e}")

# Register command handlers
application.add_handler(CommandHandler('start', start))
application.add_handler(CommandHandler('form', form_command))  # Updated /form command with web app button

# Route for receiving data from the HTML form
@app.route('/api/submit', methods=['POST'])
def receive_data():
    try:
        # Get JSON data from the form submission
        data = request.get_json()
        text = data.get('text')

        if not text:
            return jsonify({"status": "error", "message": "No text provided"}), 400

        # Send the data received from the form as a message to the bot's chat
        chat_id = 'YOUR_CHAT_ID'  # Replace with the target chat ID or update dynamically
        application.bot.send_message(chat_id=chat_id, text=f"Received from form: {text}")

        return jsonify({"status": "success", "message": "Message sent"})
    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return jsonify({"status": "error", "message": "Server error"}), 500

# Run Flask server in a separate thread to avoid blocking the bot polling
def run_flask():
    app.run(port=5000)

if __name__ == '__main__':
    # Start Flask server in a separate thread
    flask_thread = Thread(target=run_flask)
    flask_thread.start()

    # Start the Telegram bot
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
