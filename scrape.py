import requests
from bs4 import BeautifulSoup

def fetch_headlines(ticker_map):
    ticker_order = list(ticker_map.keys())
    headlines_by_ticker = {ticker: [] for ticker in ticker_order}
    sources = {
        "Investing": "https://www.investing.com/news/",
        "Yahoo": "https://finance.yahoo.com/",
        "Finviz": "https://finviz.com/news.ashx",
        "GlobeNewswire": "https://www.globenewswire.com/",
        "MarketWatch": "https://www.marketwatch.com/latest-news",
        "Reuters": "https://www.reuters.com/markets",
        "CNBC": "https://www.cnbc.com/world/?region=world",
        "Bloomberg": "https://www.bloomberg.com/markets",
        "FXStreet": "https://www.fxstreet.com/news",
        "Business Insider": "https://markets.businessinsider.com/stocks",
        "Financial Times": "https://www.ft.com/markets"
    }
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

