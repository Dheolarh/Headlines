import glob
import time
import yaml
from core.signal_parser import SignalParser
from core.scoring_engine import ScoringEngine
from core.strategy_mapper import StrategyMapper
from core.filters import Filters
from outputs.google_sheets_writer import GoogleSheetsWriter
from outputs.telegram_bot import TelegramBot
from utils.logger import logger
import os


def load_config():
    """Load configuration from credentials.yaml."""
    with open("config/credentials.yaml") as f:
        return yaml.safe_load(f)


def main():
    """Main entry point for the JMoney Engine. Initializes modules and runs the processing loop."""
    config = load_config()

    try:
        parser = SignalParser()
        scorer = ScoringEngine()
        strategy_mapper = StrategyMapper()

        google_creds = config['google_service_account_json']
        sheet_id = config['SHEET_ID']
        sheets = GoogleSheetsWriter(google_creds, sheet_id)

        telegram_config = config['telegram']
        bot = TelegramBot(
            telegram_config['bot_token'],
            telegram_config['chat_id'],
            sheets,
            timezone='America/New_York'
        )
        bot.start()

        logger.info("JMoney Engine started successfully.")

    except Exception as e:
        logger.error("Failed to initialize the engine. Shutting down.", exc_info=True)
        return

    while True:
        try:
            logger.info("Checking for new input files...")
            files = glob.glob("input_files/*.json") + glob.glob("input_files/*.csv")
            if not files:
                time.sleep(10)
                continue

            logger.info(f"Found {len(files)} new files to process.")
            all_signals = []
            for file_path in files:
                try:
                    logger.info(f"Processing file: {file_path}")
                    signals = parser.parse_file(file_path)
                    if not signals:
                        logger.warning(f"No valid signals found in {file_path}.")
                        continue
                    for signal in signals:
                        status, alert = scorer.evaluate(signal)
                        signal["status"] = status
                        signal["alert"] = alert
                        signal = strategy_mapper.apply_strategy(signal)
                        all_signals.append(signal)
                    archive_path = f"archive/{os.path.basename(file_path)}"
                    os.rename(file_path, archive_path)
                    logger.info(f"Successfully processed and archived {file_path}")
                except Exception as e:
                    logger.error(f"Failed to process file {file_path}: {e}", exc_info=True)
            if not all_signals:
                time.sleep(300)
                continue
            confirmed_signals = Filters.by_status(all_signals, "VALID")
            watchlist_signals = Filters.by_status(all_signals, "NEEDS_REVIEW")
            invalid_signals = Filters.by_status(all_signals, "INVALID")
            if confirmed_signals:
                sheets.update_sheet(confirmed_signals, "Confirmed")
            if watchlist_signals:
                sheets.update_sheet(watchlist_signals, "Watchlist")
            if invalid_signals:
                sheets.update_sheet(invalid_signals, "Invalid")
            alert_signals = Filters.for_alert(confirmed_signals)
            if alert_signals:
                bot.send_batch(alert_signals)
            logger.info("Processing cycle complete. Waiting for next interval.")
            time.sleep(300)
        except Exception as e:
            logger.error(f"An unexpected error occurred in the main loop: {e}", exc_info=True)
            time.sleep(60)

if __name__ == "__main__":
    os.makedirs("input_files", exist_ok=True)
    os.makedirs("archive", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    main()