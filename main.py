from config import TICKERS
from scrape import fetch_headlines
from classify import classify_headline
from sheet import upload_to_sheet

def main():
    import time
    import json, glob, os
    import datetime
    interval = 600  # 10 minutes in seconds
    loop_count = 1
    while True:
        print(f"\n--- Run #{loop_count} ---")
        print("Fetching news...")
        headlines = fetch_headlines(TICKERS)

        # Load JMoney scan tickers from all JSON files in input_files
        jmoney_tickers = set()
        input_dir = os.path.join("J_Money Scan", "input_files")
        for file in glob.glob(os.path.join(input_dir, "*.json")):
            try:
                with open(file, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        for entry in data:
                            ticker = entry.get("ticker")
                            if ticker:
                                jmoney_tickers.add(ticker)
            except Exception:
                pass

        print("Classifying headlines...")
        results = {}
        now = datetime.datetime.utcnow()
        for ticker, hl_list in headlines.items():
            # Volume-based boost: headlines in last 24h
            recent_headlines = []
            for item in hl_list:
                date_str = item.get("date", "")
                # Paerse Date
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
                gpt_result = classify_headline(item["headline"])
                macro_sentiments.append(gpt_result.get("category", "No News"))
            macro_total = len(macro_sentiments)
            macro_positive = sum(1 for s in macro_sentiments if s == "Positive Catalyst")
            macro_ratio = macro_positive / macro_total if macro_total else 0

            results[ticker] = []
            for item in hl_list:
                headline = item["headline"]
                source = item["source"]
                date = item["date"]
                gpt_result = classify_headline(headline)
                summary = gpt_result.get("summary", "")
                confidence = float(gpt_result.get("confidence", 0))
                sentiment = gpt_result.get("category", "No News")
                jmoney_confirmed = "JMoney Confirmed" if ticker in jmoney_tickers else ""

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
                if macro_ratio > 0.6 and sentiment == "Positive Catalyst":
                    confidence += 1
                # Recency
                confidence += recency_boost
                # Source
                confidence += source_boost
                # JMoney
                if jmoney_confirmed:
                    confidence = min(10, confidence + 2)
                confidence = min(10, max(0, round(confidence, 2)))

                results[ticker].append({
                    "ticker": ticker,
                    "headline": headline,
                    "source": source,
                    "date": date,
                    "summary": summary,
                    "sentiment": sentiment,
                    "confidence": confidence,
                    "jmoney_confirmed": jmoney_confirmed
                })
                print(f"[{ticker}] {headline} → {sentiment}, {summary}, {confidence}, {jmoney_confirmed}")

        print("Uploading to Google Sheet...")
        upload_to_sheet(results)

        # Countdown
        for i in range(interval, 0, -1):
            print(f"Fetching again in {i} seconds...", end="\r", flush=True)
            time.sleep(1)
        loop_count += 1

if __name__ == "__main__":
    main()
