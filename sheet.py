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
        sheet.append_row(["Ticker", "Headline", "Source", "Date", "Summary", "Catalyst Type", "Confidence Score", "JMoney Confirmed"])
        for ticker, headlines in data.items():
            for item in headlines:
                raw_date = item.get("date", "")
                formatted_date = raw_date
                try:
                    import datetime
                    if raw_date:
                        dt = datetime.datetime.fromisoformat(raw_date.replace("Z", ""))
                        formatted_date = dt.strftime("%Y-%m-%d %H:%M")
                except Exception:
                    pass
                sheet.append_row([
                    item.get("ticker", ""),
                    item.get("headline", ""),
                    item.get("source", ""),
                    formatted_date,
                    item.get("summary", ""),
                    item.get("sentiment", ""),
                    item.get("confidence", ""),
                    item.get("jmoney_confirmed", "")
                ])

        print("Data uploaded to Google Sheet.")
    except Exception as e:
        print(f"Google Sheet error: {e}")
