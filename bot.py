import os
import logging
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get environment variables
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Sample database of daily tips (Expand this list as much as you like)
ENGLISH_TIPS = [
    {
        "type": "Word of the Day",
        "content": "<b>Serendipity</b> (noun)<br/><i>Meaning:</i> The occurrence of valuable events by chance in a happy or beneficial way.<br/><i>Example:</i> 'We found the charming little cafe by pure serendipity.'"
    },
    {
        "type": "Grammar Tip",
        "content": "<b>Its vs. It's</b><br/>• <b>Its</b> is possessive (e.g., 'The dog wagged <i>its</i> tail').<br/>• <b>It's</b> is a contraction of 'it is' or 'it has' (e.g., '<i>It's</i> raining outside')."
    },
    {
        "type": "Idiom of the Day",
        "content": "<b>Bite the bullet</b><br/><i>Meaning:</i> To face a difficult situation with courage and get it over with.<br/><i>Example:</i> 'I hate going to the dentist, but I just need to <i>bite the bullet</i> and go.'"
    }
]

# Track subscribed chat IDs (For a production app, use a database like SQLite or PostgreSQL)
# For this basic background worker, it keeps active users in memory
subscribed_users = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends a welcome message and registers the user for daily updates."""
    chat_id = update.effective_chat.id
    subscribed_users.add(chat_id)
    
    welcome_text = (
        "<b>💡 Welcome to LingoBiteBot!</b>\n\n"
        "You are now subscribed. I will send you exactly one curated English word, "
        "idiom, or essential grammar tip delivered straight to your chat every day."
    )
    # Using HTML parse mode to ensure stable rendering
    await context.bot.send_message(chat_id=chat_id, text=welcome_text, parse_mode="HTML")

async def send_daily_tip(application: Application):
    """Broadcasts a random English tip to all subscribed users."""
    if not subscribed_users:
        logger.info("No active subscribers to send updates to.")
        return

    tip = random.choice(ENGLISH_TIPS)
    message = f"<b>🚀 Your Daily {tip['type']}</b>\n\n{tip['content']}"

    for chat_id in list(subscribed_users):
        try:
            await application.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")
            logger.info(f"Successfully sent daily tip to {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send message to {chat_id}: {e}")

def main() -> None:
    """Start the bot."""
    if not TOKEN:
        logger.error("No TELEGRAM_BOT_TOKEN found in environment variables!")
        return

    # Build the application
    application = Application.builder().token(TOKEN).build()

    # Register the /start command
    application.add_handler(CommandHandler("start", start))

    # Set up the Background Scheduler for the daily broadcast
    scheduler = BackgroundScheduler()
    # Triggers every day at 09:00 AM. Adjust hours/minutes as preferred.
    scheduler.add_job(
        lambda: application.loop.create_task(send_daily_tip(application)),
        "cron",
        hour=9,
        minute=0
    )
    scheduler.start()
    logger.info("Background scheduler started successfully.")

    # Run the bot using polling
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
