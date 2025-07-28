# Catalyst News & JMoney Scan Integration

## Overview
This project automatically scrapes financial news headlines for selected tickers, classifies and summarizes them using GPT-4o, applies adaptive scoring logic, and uploads the results to a Google Sheet. It also cross-references technical signals from the JMoney scan engine for confirmation.

## Features
- **News Scraping:** Fetches headlines for TSLA, OKLO, AAPL, and URBN from multiple financial news sources every 10 minutes.
- **Classification & Summarization:** Uses GPT-4o to classify each headline (Positive/Negative/Neutral), generate a short summary, and assign a confidence score (0–10).
- **Adaptive Scoring:** Confidence is boosted based on:
  - Volume of recent headlines
  - Recency of news
  - Source reliability
  - Macro context (trend of recent headlines)
  - JMoney scan confirmation
- **JMoney Scan Integration:** Dynamically scans all JSON files in `J_Money Scan/input_files` for tickers. If a ticker is present in both news and JMoney scan, it is marked as "JMoney Confirmed" and receives a confidence boost.
- **Google Sheets Output:** Results are uploaded to a Google Sheet with columns: Ticker, Headline, Source, Date, Summary, Catalyst Type, Confidence Score, JMoney Confirmed.
- **Continuous Operation:** The script runs in a loop, fetching and uploading every 10 minutes, with a live countdown.
- **Duplicate Prevention:** Avoids duplicate headlines in each run.

## Setup
1. **Install requirements:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure API keys and settings:**
   - Edit `config.py` with your OpenAI API key and Google service account JSON.
3. **Google Sheets:**
   - Share your Google Sheet with the service account email from your credentials JSON.
4. **JMoney Scan:**
   - Place your JMoney scan JSON files in `J_Money Scan/input_files/`.

## Usage
Run the main script:
```bash
python main.py
```
The script will fetch, classify, and upload news every 10 minutes. You can stop it with Ctrl+C.

## Customization
- **Tickers:** Edit the `TICKERS` dictionary in `config.py`.
- **Interval:** Change the `interval` variable in `main.py` (in seconds).
- **News Sources:** Edit the `sources` dictionary in `scrape.py`.

## Notes
- The date/time in the sheet is in UTC, formatted as `YYYY-MM-DD HH:MM`.
- The project is robust to changes in JMoney scan files and will always use the latest tickers.
- Adaptive scoring logic can be further customized as needed.
