import os
import sys
import threading
import time
import json
import glob
import datetime

from dotenv import load_dotenv
load_dotenv()

import requests
from config import TICKERS
from scrape import fetch_headlines
from classify import classify_headline
from sheet import upload_to_sheet
from telegram_bot import send_telegram_message, handle_clear_command

# Set GOOGLE_APPLICATION_CREDENTIALS from .env if present, else print a warning
gsa_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
if gsa_path and os.path.exists(gsa_path):
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = gsa_path
else:
    print("Warning: GOOGLE_APPLICATION_CREDENTIALS not set or file not found:", gsa_path)


# Log outputs to terminal and output file
class Tee:
    def __init__(self, *files):
        self.files = files
    def write(self, obj):
        for f in self.files:
            f.write(obj)
            f.flush()
    def flush(self):
        for f in self.files:
            f.flush()

logfile = open("output.log", "a", encoding="utf-8", buffering=1)
sys.stdout = Tee(sys.__stdout__, logfile)
sys.stderr = Tee(sys.__stderr__, logfile)


def fetch_and_process(loop_count=None):
    print("[STEP 1] Run: Starting new cycle: fetching and processing headlines...")
    if loop_count:
        print(f"\n--- Run #{loop_count} ---")
    print("[STEP 2] Fetching news for all tickers...")
    from config import TICKERS
    from scrape import fetch_headlines
    from classify import classify_headline
    from sheet import upload_to_sheet
    from telegram_bot import send_telegram_message, handle_clear_command
    headlines = fetch_headlines(TICKERS)

    # Load JMoney signals from Google Sheet 'Jmoney_engine'
    import gspread
    from oauth2client.service_account import ServiceAccountCredentials
    from config import GOOGLE_SERVICE_ACCOUNT_JSON
    jmoney_tickers = set()
    jmoney_details = {}
    try:
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE_SERVICE_ACCOUNT_JSON, scope)
        client = gspread.authorize(creds)
        sheet = client.open("Jmoney_Engine").worksheet("Confirmed")
        rows = sheet.get_all_records()
        for row in rows:
            ticker = row.get("ticker")
            if ticker:
                jmoney_tickers.add(ticker)
                jmoney_details[ticker] = row
    except Exception as e:
        print(f"[JMoney Sheet Error] {e}")

    print("[STEP 3] All headlines fetched. Now analyzing and processing...")
    results = {}
    now = datetime.datetime.utcnow()
    for ticker, hl_list in headlines.items():
        print(f"[STEP 4] Processing ticker: {ticker}")
        # [Analyze] Looping through tickers and headlines for analysis
        # Volume-based boost: headlines in last 24h
        recent_headlines = []
        for item in hl_list:
            date_str = item.get("date", "")
            # Try to parse date
            try:
                if date_str:
                    dt = datetime.datetime.fromisoformat(date_str.replace("Z", ""))
                else:
                    dt = None
            except Exception:
                dt = None
            if dt and (now - dt).total_seconds() < 86400:
                recent_headlines.append(item)
        volume_boost = len(recent_headlines) > 3

        # Macro context: % positive in last 24h
        macro_positive = 0
        macro_total = 0
        macro_sentiments = []
        for item in recent_headlines:
            print("[STEP 5] Analyzing macro context for recent headline...")
            gpt_result = classify_headline(item["headline"])
            macro_sentiments.append(gpt_result.get("category", "No News"))
        macro_total = len(macro_sentiments)
        macro_positive = sum(1 for s in macro_sentiments if s == "Positive Catalyst")
        macro_ratio = macro_positive / macro_total if macro_total else 0

        results[ticker] = []
        for item in hl_list:
            print("[STEP 6] Analyzing individual headline and applying JMoney logic...")
            headline = item["headline"]
            source = item["source"]
            date = item["date"]
            # Format date for Telegram and Google Sheet output
            formatted_date = date
            try:
                if date:
                    dt = datetime.datetime.fromisoformat(date.replace("Z", ""))
                    formatted_date = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                pass
            # Compose JMoney context for GPT filtering
            jmoney_context = None
            if ticker in jmoney_details:
                entry = jmoney_details[ticker]
                jmoney_context = {
                    "macro_score": entry.get("macro_score", ""),
                    "sentiment": entry.get("sentiment", ""),
                    "ZS10_score": entry.get("ZS10_score", ""),
                    "strategy": entry.get("strategy", ""),
                    "signal_type": entry.get("signal_type", "")
                }
            gpt_result = classify_headline(headline, jmoney_context)
            print("[STEP 7] GPT classification complete.")
            summary = gpt_result.get("summary", "")
            confidence = float(gpt_result.get("confidence", 0))
            news_decision = gpt_result.get("category", "No News")
            filter_decision = gpt_result.get("filter_decision", False)
            # Catalyst type: only positive/negative/neutral if filter_decision is True, else Neutral
            if filter_decision:
                print("[STEP 8] Headline passed filter decision.")
                catalyst_type = "Positive Catalyst" if news_decision == "Positive Catalyst" else ("Negative Catalyst" if news_decision == "Negative Catalyst" else "Neutral")
            else:
                catalyst_type = "Neutral"

            # JMoney confirmation: confirmed if ticker is present in Confirmed tab
            zs10_score = macro_score = strategy = signal_type = comment = sentiment_score = ""
            jmoney_confirmed = ""
            jmoney_note = ""
            if ticker in jmoney_details:
                print("[STEP 9] JMoney context found, marking as confirmed (no extra checks)...")
                entry = jmoney_details[ticker]
                zs10_score = entry.get("ZS10_score", "")
                macro_score = entry.get("macro_score", "")
                strategy = entry.get("strategy", "")
                signal_type = entry.get("signal_type", "")
                comment = entry.get("comment", "")
                sentiment_score = entry.get("sentiment", "")
                jmoney_confirmed = "✅ JMoney Confirmed"
                jmoney_note = "Confirmed: Ticker present in JMoney Confirmed tab."

            # Adaptive logic
            # Recency weight
            recency_boost = 0
            try:
                if date:
                    dt = datetime.datetime.fromisoformat(date.replace("Z", ""))
                    if (now - dt).total_seconds() < 86400:
                        recency_boost = 0.5
            except Exception:
                pass
            # Source reliability
            source_boost = 0
            if source in ["MarketWatch", "Reuters"]:
                source_boost = 1
            elif source == "Finviz":
                source_boost = -0.5
            # Volume-based boost
            if volume_boost:
                confidence += 1
            # Macro context boost
            if macro_ratio > 0.6 and news_decision == "Positive Catalyst":
                confidence += 1
            # Recency
            confidence += recency_boost
            # Source
            confidence += source_boost
            # JMoney
            if jmoney_confirmed:
                confidence = min(10, confidence + 2)
            confidence = min(10, max(0, round(confidence, 2)))


            # Visual flag based on confidence
            if confidence >= 8:
                flag = "🟢"
            elif confidence >= 5:
                flag = "🟡"
            else:
                flag = "🔴"

            results[ticker].append({
                "ticker": ticker,
                "headline": headline,
                "source": source,
                "date": date,
                "summary": summary,
                "news_decision": news_decision,
                "catalyst_type": catalyst_type,
                "confidence": confidence,
                "flag": flag,
                "jmoney_confirmed": jmoney_confirmed,
                "zs10_score": zs10_score,
                "macro_score": macro_score,
                "strategy": strategy,
                "signal_type": signal_type,
                "jmoney_comment": comment,
                "jmoney_note": jmoney_note
            })
            print(f"[STEP 11] Output: {flag} | {ticker} | {headline} | {summary} | {confidence} | {jmoney_confirmed} | ZS10: {zs10_score} | Macro: {macro_score} | Strategy: {strategy} | Signal: {signal_type}")
            # Telegram output
            telegram_msg = (
                f"{flag} <b>{ticker}</b>\n"
                f"<b>Headline:</b> {headline}\n"
                f"<b>Summary:</b> {summary}\n"
                f"<b>Decision:</b> {news_decision} | <b>Type:</b> {catalyst_type}\n"
                f"<b>Confidence:</b> {confidence}/10\n"
                f"<b>Source:</b> {source}\n"
                f"<b>Date:</b> {formatted_date}\n"
                f"<b>JMoney:</b> {jmoney_confirmed} {jmoney_note}\n"
                f"<b>ZS10:</b> {zs10_score} | <b>Macro:</b> {macro_score} | <b>Strategy:</b> {strategy} | <b>Signal:</b> {signal_type}\n"
            )
            send_telegram_message(telegram_msg)

    print("[STEP 12] Output: Uploading results to Google Sheet...")
    upload_to_sheet(results)

def poll_for_commands():
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    last_update_id = None
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 30}
        if last_update_id:
            params["offset"] = last_update_id + 1
        try:
            resp = requests.get(url, params=params, timeout=35)
            if not resp.ok:
                time.sleep(10)
                continue
            updates = resp.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message")
                if not message:
                    continue
                text = message.get("text", "")
                if text.strip() == "/clear":
                    from telegram_bot import send_telegram_message, handle_clear_command
                    send_telegram_message("Clearing all messages (admin only)...")
                    handle_clear_command()
                elif text.strip() == "/fetchnow":
                    from telegram_bot import send_telegram_message
                    send_telegram_message("Manual fetch triggered!")
                    threading.Thread(target=fetch_and_process, kwargs={"loop_count":None}, daemon=True).start()
        except Exception as e:
            print(f"[TelegramBotRunner] Error: {e}")
        time.sleep(5)

def main():
    threading.Thread(target=poll_for_commands, daemon=True).start()
    loop_count = 1
    while True:
        fetch_and_process(loop_count=loop_count)
        interval = 3600  # 1 hour
        for i in range(interval, 0, -1):
            print(f"Fetching again in {i} seconds...", end="\r", flush=True)
            time.sleep(1)
        loop_count += 1

if __name__ == "__main__":
    main()
