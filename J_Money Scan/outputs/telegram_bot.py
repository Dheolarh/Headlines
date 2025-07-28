import telegram
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from utils.logger import logger
from apscheduler.schedulers.background import BackgroundScheduler
import gspread
import pytz
from utils.helpers import format_signal_message

class TelegramBot:
    """Telegram bot for sending trading signals and handling commands."""
    def __init__(self, token, chat_id, sheets_writer, timezone='UTC'):
        self.token = token
        self.chat_id = chat_id
        self.bot = telegram.Bot(token=token)
        self.updater = Updater(token, use_context=True)
        self.sheets_writer = sheets_writer
        self.timezone = pytz.timezone(timezone)
        self.scheduler = BackgroundScheduler(timezone=self.timezone)

    def start(self):
        """Start the Telegram bot and scheduler."""
        self.setup_handlers()
        self.scheduler.add_job(self.send_daily_summary, 'cron', hour=7, minute=0)
        self.scheduler.start()
        logger.info("Telegram bot and scheduler started")
        self.updater.start_polling()

    def setup_handlers(self):
        """Set up command and message handlers for the bot."""
        dp = self.updater.dispatcher
        dp.add_handler(CommandHandler("today", self.send_today_signals))
        dp.add_handler(CommandHandler("zen", self.send_strategy_signals))
        dp.add_handler(CommandHandler("boost", self.send_strategy_signals))
        dp.add_handler(CommandHandler("watchlist", self.send_watchlist))
        dp.add_handler(CommandHandler("invalid", self.send_invalid_signals))
        dp.add_handler(CommandHandler("clear", self.clear_chat))
        dp.add_handler(MessageHandler(Filters.command, self.unknown_command))

    def get_signals_from_sheet(self, sheet_name, strategy_filter=None):
        """Fetch signals from a specific sheet, optionally filtered by strategy."""
        try:
            worksheet = self.sheets_writer.sheet.worksheet(sheet_name)
            records = worksheet.get_all_records()
            if not records:
                return f"No signals found in {sheet_name}."
            if strategy_filter:
                strategy_filter = strategy_filter.lower()
                filtered_records = [
                    r for r in records if str(r.get('strategy', '')).lower() == strategy_filter
                ]
                if not filtered_records:
                    return f"No {strategy_filter.capitalize()} signals found in {sheet_name}."
                records = filtered_records
            messages = [format_signal_message(record) for record in records]
            return "\n\n---\n\n".join(messages)
        except gspread.WorksheetNotFound:
            return f"No sheet found with the name: {sheet_name}"
        except Exception as e:
            logger.error(f"Error fetching signals from sheet '{sheet_name}': {e}", exc_info=True)
            return f"An error occurred while fetching signals for {sheet_name}."

    def send_daily_summary(self):
        """Send a summary of all signals from the 'Confirmed' sheet."""
        logger.info("Scheduler triggered: sending daily summary.")
        message = self.get_signals_from_sheet("Confirmed")
        self.bot.send_message(chat_id=self.chat_id, text=message, parse_mode="HTML")

    def send_today_signals(self, update, context):
        """Send today's signals from the 'Confirmed' sheet."""
        message = self.get_signals_from_sheet("Confirmed")
        chat_id = update.effective_chat.id
        self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    def send_strategy_signals(self, update, context):
        """Send signals from the 'Confirmed' sheet filtered by strategy."""
        strategy_name = update.message.text[1:]
        message = self.get_signals_from_sheet("Confirmed", strategy_filter=strategy_name)
        chat_id = update.effective_chat.id
        self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    def send_watchlist(self, update, context):
        """Send signals from the 'Watchlist' sheet."""
        message = self.get_signals_from_sheet("Watchlist")
        chat_id = update.effective_chat.id
        self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    def send_invalid_signals(self, update, context):
        """Send signals from the 'Invalid' sheet."""
        message = self.get_signals_from_sheet("Invalid")
        chat_id = update.effective_chat.id
        self.bot.send_message(chat_id=chat_id, text=message, parse_mode="HTML")

    def clear_chat(self, update, context):
        """Delete all previous messages in the chat (if bot has permission)."""
        chat_id = update.effective_chat.id
        try:
            for message in context.bot.get_chat(chat_id).get_history():
                try:
                    context.bot.delete_message(chat_id=chat_id, message_id=message.message_id)
                except Exception:
                    continue
            context.bot.send_message(chat_id=chat_id, text="Chat cleared.")
        except Exception as e:
            logger.error(f"Failed to clear chat: {e}")
            context.bot.send_message(chat_id=chat_id, text="Failed to clear chat or insufficient permissions.")

    def unknown_command(self, update, context):
        """Handle unknown commands."""
        context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Sorry, I didn't understand that command."
        )

    def send_alert(self, signal):
        """Send an alert for a single signal."""
        message = format_signal_message(signal)
        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="HTML"
            )
            logger.info(f"Sent Telegram alert for {signal.get('ticker')}")
        except Exception as e:
            logger.error(f"Telegram send error: {e}")

    def send_batch(self, signals):
        """Send alerts for a batch of signals."""
        for signal in signals:
            self.send_alert(signal)