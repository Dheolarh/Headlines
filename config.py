import os
import json

OPENAI_API_KEY = os.getenv("OPENAI_KEY", "")
GOOGLE_SERVICE_ACCOUNT_JSON = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "") or os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")
SHEET_NAME = os.getenv("SHEET_NAME", "")

# Load tickers from config/tickers.json
with open(os.path.join(os.path.dirname(__file__), "config", "tickers.json"), "r") as f:
    TICKERS = json.load(f)
