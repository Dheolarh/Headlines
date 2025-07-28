from oauth2client.service_account import ServiceAccountCredentials
from utils.logger import logger
import time
import json
from datetime import datetime
import os
import gspread

class GoogleSheetsWriter:
    """Handles writing signals to Google Sheets."""
    def __init__(self, creds_dict, sheet_id):
        """Initialize the Google Sheets writer with credentials and sheet ID."""
        self.creds_file = "temp_google_creds.json"
        self.sheet = None
        self.processed_ids = set()
        try:
            logger.info("Authorizing with Google Sheets...")
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]
            with open(self.creds_file, "w") as f:
                json.dump(creds_dict, f)
            creds = ServiceAccountCredentials.from_json_keyfile_name(self.creds_file, scope)
            client = gspread.authorize(creds)
            logger.info("Authorization successful. Opening sheet...")
            self.sheet = client.open_by_key(sheet_id)
            logger.info(f"Successfully opened sheet: '{self.sheet.title}'")
            self.processed_ids = self.get_all_processed_ids()
        except Exception as e:
            logger.error(f"Failed to initialize GoogleSheetsWriter: {e}", exc_info=True)
            raise

    def __del__(self):
        """Clean up temporary credentials file on deletion."""
        if os.path.exists(self.creds_file):
            os.remove(self.creds_file)

    def get_all_processed_ids(self):
        """Fetch all processed signal IDs from all sheets except meta."""
        logger.info("Fetching all processed signal IDs from sheets...")
        processed_ids = set()
        for worksheet in self.sheet.worksheets():
            if 'meta' not in worksheet.title.lower():
                try:
                    signal_ids = worksheet.col_values(1)[1:]
                    processed_ids.update(signal_ids)
                except Exception as e:
                    logger.warning(f"Could not read IDs from '{worksheet.title}': {e}")
        logger.info(f"Found {len(processed_ids)} existing signal IDs.")
        return processed_ids

    def update_sheet(self, signals, tab_name):
        """Update a specific sheet tab with new signals."""
        if not self.sheet:
            logger.error("Google Sheet not available. Cannot update.")
            return
        if not signals:
            return
        logger.info(f"Attempting to update '{tab_name}' with {len(signals)} signals...")
        try:
            worksheet = self.sheet.worksheet(tab_name)
            logger.info(f"Worksheet '{tab_name}' found.")
        except gspread.WorksheetNotFound:
            logger.info(f"Worksheet '{tab_name}' not found. Creating it...")
            worksheet = self.sheet.add_worksheet(title=tab_name, rows=100, cols=20)
        preferred_order = [
            "ticker", "asset_type", "price", "macro_score", "score", "sentiment", "direction", "entry_zone",
            "stop_loss", "tp1", "tp2", "tp_strategy", "status"
        ]
        all_headers_set = set().union(*(s.keys() for s in signals))
        all_headers_set.update(preferred_order)
        all_headers = [col for col in preferred_order if col in all_headers_set]
        all_headers += [col for col in sorted(all_headers_set) if col not in preferred_order]
        existing_headers = worksheet.row_values(1) if worksheet.row_count > 0 else []
        if existing_headers != all_headers:
            logger.info("Updating headers...")
            worksheet.update([all_headers], 'A1')
        new_signals = [s for s in signals if s.get("signal_id") not in self.processed_ids]
        if not new_signals:
            logger.info("No new signals to add.")
            return
        logger.info(f"Preparing to add {len(new_signals)} new rows...")
        rows = [[s.get(header, "") for header in all_headers] for s in new_signals]
        worksheet.append_rows(rows, value_input_option='USER_ENTERED')
        logger.info(f"Successfully added {len(rows)} new signals to '{tab_name}'.")
        self.processed_ids.update(s["signal_id"] for s in new_signals)
        self.update_meta_sheet(new_signals)

    def update_meta_sheet(self, signals):
        """Update the Meta sheet with new signal IDs and timestamps."""
        logger.info(f"Updating Meta sheet with {len(signals)} new entries...")
        try:
            meta_sheet = self.sheet.worksheet("Meta")
        except gspread.WorksheetNotFound:
            meta_sheet = self.sheet.add_worksheet(title="Meta", rows=100, cols=2)
            meta_sheet.append_row(["signal_id", "processed_at"])
        rows = [[s["signal_id"], datetime.now().isoformat()] for s in signals]
        meta_sheet.append_rows(rows, value_input_option='USER_ENTERED')
        logger.info("Meta sheet updated successfully.")