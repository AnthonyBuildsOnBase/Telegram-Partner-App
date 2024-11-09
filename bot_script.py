import os
import logging
import json
import csv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler, MessageHandler, filters
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
BOT_API_KEY = os.getenv('TELEGRAM_API_TOKEN')
WEB_APP_URL = os.getenv('WEB_APP_URL')

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Initialize bot
application = ApplicationBuilder().token(BOT_API_KEY).build()

# CSV file to store user info
USER_DATA_FILE = 'user_data.csv'

# Function to save username and chat_id to CSV
def save_user_data(username, chat_id):
    file_exists = os.path.isfile(USER_DATA_FILE)
    with open(USER_DATA_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["username", "chat_id"])  # Write header if file doesn't exist
        writer.writerow([username.strip().lower(), chat_id])

# /optin command handler to save username and chat_id
async def optin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    username = update.effective_user.username
    chat_id = update.effective_chat.id
    if username and chat_id:
        save_user_data(username, chat_id)
        await context.bot.send_message(chat_id=chat_id, text="You've opted in! We have saved your username and chat ID.")
        logging.info(f"Saved username: {username}, chat_id: {chat_id}")
    else:
        await context.bot.send_message(chat_id=chat_id, text="Could not save your data. Please make sure you have a username set.")

# /form command handler to open the Web App
async def form_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.info("Received /form command")
    keyboard = [[InlineKeyboardButton("Open Form", web_app=WebAppInfo(WEB_APP_URL))]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Click below to open the form:", reply_markup=reply_markup)

# Handler for data sent from the Web App
# Handler for data sent from the Web App
async def web_app_data_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.debug(f"Received an update: {update.to_dict()}")
    try:
        logging.info("Processing update in web_app_data_handler")

        # Check if update contains web_app_data
        if update.message and update.message.web_app_data:
            web_app_data = update.message.web_app_data.data
            logging.debug(f"Web App data received: {web_app_data}")
            
            # Parse the JSON data
            data = json.loads(web_app_data)
            username = data.get("username")
            text = data.get("text", "No text received")

            # Check if the username was provided
            if username is None:
                logging.error("No username provided in Web App data.")
                await update.message.reply_text("Error: No username provided. Please enter a valid username.")
                return

            # Normalize username by stripping whitespace and converting to lowercase
            username = username.strip().lower()

            # Look up chat_id for the provided username
            chat_id = None
            with open(USER_DATA_FILE, mode='r', newline='') as file:
                reader = csv.DictReader(file)
                for row in reader:
                    if row["username"].strip().lower() == username:
                        chat_id = row["chat_id"]
                        break
            
            if chat_id:
                # Send message to the user with the provided username
                await application.bot.send_message(chat_id=int(chat_id), text=f"Received from form: {text}")
                logging.info(f"Message sent successfully to {username}")
                # Inform the sender that the message was sent
                await update.message.reply_text(f"Your message has been sent to @{username}.")
            else:
                logging.error(f"Username '{username}' not found in CSV.")
                await update.message.reply_text(f"Username '@{username}' not found. Make sure the user has opted in.")
        else:
            logging.error("No Web App data found in this update.")
            await update.message.reply_text("Error: No data received from the Web App.")
    except Exception as e:
        logging.error(f"Error processing Web App data: {e}")
        await update.message.reply_text("An error occurred while processing your request.")


# Register command handlers
application.add_handler(CommandHandler('optin', optin))
application.add_handler(CommandHandler('form', form_command))

# Use filters.ALL to capture all types of messages and updates
application.add_handler(MessageHandler(filters.ALL, web_app_data_handler))

# Start the bot with polling
if __name__ == '__main__':
    logging.info("Starting Telegram bot with polling")
    try:
        application.run_polling()
    except KeyboardInterrupt:
        logging.info("Bot stopped by user.")
    except Exception as e:
        logging.error(f"Error occurred: {e}")
