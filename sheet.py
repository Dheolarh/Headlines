import gspread
from oauth2client.service_account import ServiceAccountCredentials
from config import GOOGLE_SERVICE_ACCOUNT_JSON, SHEET_NAME

def upload_to_sheet(data):
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SERVICE_ACCOUNT_JSON, scope)
        client = gspread.authorize(creds)

        sheet = client.open(SHEET_NAME).sheet1
        sheet.clear()
        # Added "Strategy", "Signal ID", and "Watch" columns
        sheet.append_row([
            "Ticker", "Headline", "Source", "Date", "Summary", "News Decision", "Catalyst Type",
            "Confidence Score", "Visual Flag", "JMoney Confirmed", "Macro Score",
            "Strategy", "Signal ID", "JMoney Note"
        ])
        # Read all existing rows for deduplication and update
        all_rows = sheet.get_all_values()
        headers = all_rows[0] if all_rows else []
        existing = {(row[0], row[1]): idx for idx, row in enumerate(all_rows[1:], 2) if len(row) >= 2}  # (ticker, headline): row number
        for ticker, headlines in data.items():
            for item in headlines:
                raw_date = item.get("date", "")
                date = raw_date
                try:
                    import datetime
                    if raw_date:
                        dt = datetime.datetime.fromisoformat(raw_date.replace("Z", ""))
                        date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                # Add strategy, signal_id, and watch
                row_data = [
                    item.get("ticker", ""),
                    item.get("headline", ""),
                    item.get("source", ""),
                    date,
                    item.get("summary", ""),
                    item.get("news_decision", ""),
                    item.get("catalyst_type", ""),
                    item.get("confidence", ""),
                    item.get("flag", ""),
                    item.get("jmoney_confirmed", ""),
                    item.get("macro_score", ""),
                    item.get("strategy", ""),
                    item.get("signal_type", ""),
                    item.get("jmoney_note", "")
                ]
                sheet.append_row(row_data)
    except Exception as e:
        print(f"[Sheet Upload Error] {e}")
