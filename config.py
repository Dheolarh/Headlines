import os

OPENAI_API_KEY = os.getenv("OPENAI_KEY", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SHEET_NAME = os.getenv("SHEET_NAME", "")
TICKERS = {
    "OKLO": ["OKLO", "Oklo Inc"],
    "URBN": ["URBN", "Urban Outfitters"],
    "TSLA": ["TSLA", "Tesla"],
    "AAPL": ["AAPL", "Apple"],
    "BTC/USD": ["BTC/USD", "Bitcoin"],
    "GOLD": ["GOLD", "Gold"],
    "SILVER": ["SILVER", "Silver"],
    "EURO/USD": ["EURO/USD", "Euro Dollar"],
    "SPX": ["SPX", "S&P 500"],
    "WTI": ["WTI", "Crude Oil"],
    "USD/CHF": ["USD/CHF", "US Dollar Swiss Franc"]
}
