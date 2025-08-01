import requests
from bs4 import BeautifulSoup
import os
import json

def fetch_headlines(ticker_map):
    ticker_order = list(ticker_map.keys())
    headlines_by_ticker = {ticker: [] for ticker in ticker_order}

    # Load sources from config/sources.json
    sources_path = os.path.join(os.path.dirname(__file__), "config", "sources.json")
    with open(sources_path, "r") as f:
        sources = json.load(f)

    import datetime
    seen_headlines = set()
    for name, url in sources.items():
        try:
            response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
            soup = BeautifulSoup(response.text, "html.parser")
            articles = soup.find_all(["h3", "a", "p"])

            for tag in articles:
                text = tag.get_text(strip=True)
                date = datetime.datetime.utcnow().isoformat() + 'Z'
                if text in seen_headlines:
                    continue
                seen_headlines.add(text)
                for ticker in ticker_order:
                    aliases = ticker_map.get(ticker, [])
                    for alias in aliases:
                        if alias.lower() in text.lower():
                            headlines_by_ticker[ticker].append({
                                "headline": text,
                                "source": name,
                                "date": date
                            })
                            break
        except Exception as e:
            print(f"[{name}] Failed to fetch: {e}")
    return headlines_by_ticker

