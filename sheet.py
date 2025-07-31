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
        sheet.append_row(["Ticker", "Headline", "Source", "Date", "Summary", "News Decision", "Catalyst Type", "Confidence Score", "Visual Flag", "JMoney Confirmed"])
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
                    item.get("jmoney_confirmed", "")
                ]
                key = (item.get("ticker", ""), item.get("headline", ""))
                if key in existing:
                    # Check if JMoney fields have changed; if so, update row
                    row_num = existing[key]
                    old_row = all_rows[row_num-1] if row_num-1 < len(all_rows) else []
                    # Compare macro_score, zs10_score, strategy, signal_type, jmoney_confirmed
                    changed = False
                    for col, field in zip([8], ["jmoney_confirmed"]):
                        idx = headers.index("JMoney Confirmed") if "JMoney Confirmed" in headers else -1
                        if idx != -1 and (len(old_row) <= idx or old_row[idx] != item.get(field, "")):
                            changed = True
                    if changed:
                        sheet.update(f"A{row_num}:I{row_num}", [row_data])
                else:
                    sheet.append_row(row_data)

        print("Data uploaded to Google Sheet.")
    except Exception as e:
        print(f"Google Sheet error: {e}")
