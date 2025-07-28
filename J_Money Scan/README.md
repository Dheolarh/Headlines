# JMoney Trading Engine

An automated, AI-driven trading signal processing system designed to parse
structured signal data, synchronize it with Google Sheets for tracking, and
deliver real-time alerts via a Telegram bot.

---

## System Overview

The engine is built to be a robust pipeline for trading signals:

- **Input:** Monitors the `input_files/` directory for new signal files in
  `.json` or `.csv` format.
- **Parsing & Validation:** Each signal is parsed, standardized against a common
  format, and validated to ensure it has all required data fields (e.g., ticker,
  score, direction).
- **Scoring:** Signals are evaluated against configurable thresholds
  (`config/thresholds.json`) to determine their status:
  - **VALID:** High-confidence signals that meet all criteria.
  - **NEEDS_REVIEW:** Promising signals that don't meet strict criteria for
    immediate action.
  - **INVALID:** Signals missing required data or with very low scores.
- **Output:** Processed signals are written to a shared Google Sheet, sorted
  into different tabs (Confirmed, Watchlist, Invalid) for easy tracking.
- **Alerting:** High-confidence (VALID) signals trigger an immediate alert via
  Telegram. The bot also provides on-demand access to all signal categories.

---

## Features

- **Multi-Source Processing:** Ingests signals from various '.json'data
- **Dynamic Field Mapping:** Uses `config/field_mappings.json` to standardize
  diverse input data into a consistent internal format.
- **Real-time Google Sheets Sync:** Automatically creates and updates Confirmed,
  Watchlist, and Invalid tabs in a Google Sheet.
- **Automated Telegram Alerts:** Delivers daily summaries and on-demand reports
  through a responsive Telegram bot.
- **Configurable Logic:** Easily adjust scoring thresholds, strategy parameters,
  and API credentials through simple configuration files.

## Required Fields for Signal JSON Files

Every JSON file must contain records with the following required fields to be
processed:

- `ticker`: The symbol or identifier for the asset (e.g., "AAPL", "EUR/JPY").
- `score`: The confidence or score value for the signal (numeric).
- `macro_score`: The macroeconomic or context score (numeric).
- `direction`: The trade direction or bias (e.g., "↑", "↓", "Long", "Short").

If any of these fields are missing in a record, that record will be skipped and
a warning will be logged.

---

## Installation and Setup

Follow these steps to get the trading engine running on your local machine.

### 1. Requirements

- Python 3.8+
- A Google Cloud Platform (GCP) project with the Google Sheets API and Google
  Drive API enabled.
- A Telegram Bot created via the BotFather.

### 2. Installation

Clone the project repository and install the required Python packages:

```bash
# Navigate to your desired directory
git clone <your-repository-url>
cd jmoney_engine

# Install all required packages
pip install -r requirements.txt
```

### 3. Credentials Setup

This is the most critical step. The engine requires credentials for Google
Sheets and Telegram.

#### A. Google Sheets Credentials

**Generate Service Account Key:**

1. Go to your Google Cloud Console.
2. Navigate to "APIs & Services" > "Credentials".
3. Create a new Service Account.
4. Once created, go to the "Keys" tab and create a new key.
5. Choose JSON as the key type. A `google_service_account.json` file will be
   downloaded.

**Configure `credentials.yaml`:**

- Open the downloaded `google_service_account.json` file.
- Open the `config/credentials.yaml` file in the project.
- Copy the entire content of the `.json` file and paste it under the
  `google_service_account_json:` section in `credentials.yaml`. Ensure the
  indentation is correct.

Example:

```yaml
google_service_account_json:
   "type": "service_account"
   "project_id": "your-gcp-project-id"
   "private_key_id": "your-private-key-id"
   "private_key": "-----BEGIN PRIVATE KEY-----\n...your-private-key...\n-----END PRIVATE KEY-----\n"
   "client_email": "your-bot-email@your-gcp-project-id.iam.gserviceaccount.com"
   # ... and so on for the rest of the JSON content
```

**Share Your Google Sheet:**

- In your `credentials.yaml` file, find the `client_email` address of your bot.
- Open your target Google Sheet.
- Click the "Share" button.
- Paste the bot's `client_email` into the sharing dialog and give it Editor
  permissions. This is required for the script to be able to write data to the
  sheet.

#### B. Telegram Credentials

- **Get Bot Token:** Talk to the BotFather on Telegram to create a new bot and
  get your unique API token.
- **Get Chat ID:** Talk to the [@userinfobot](https://t.me/userinfobot) on
  Telegram to get your personal Chat ID.
- **Configure `credentials.yaml`:** Add your Bot Token and Chat ID to the
  `telegram:` section of `config/credentials.yaml`.

Example:

```yaml
telegram:
   bot_token: "<your-bot-token>"
   chat_id: "<your-chat-id>"
```

#### C. Sheet ID in credentials.yaml

Add your Google Sheet ID to the top level of your `config/credentials.yaml`
file:

Example:

```yaml
SHEET_ID: <your-sheet-id>
```

---

## How to Run the Engine

Once the installation and configuration are complete, you can start the engine
with a single command from the project's root directory:

```bash
python main.py
```

The script will:

- Initialize all modules.
- Connect to Google Sheets and Telegram.
- Start monitoring the `input_files/` directory for new signal files.

To run the engine, simply place any `.json` or `.csv` signal files into the
`input_files/` directory. The engine will automatically process them.

---

## Telegram Commands

You can interact with the bot on Telegram using the following commands:

- `/today`: Shows all high-confidence signals from the "Confirmed" sheet.
- `/watchlist`: Displays all signals from the "Watchlist" sheet.
- `/invalid`: Shows all signals that failed validation from the "Invalid" sheet.
- `/zen` or `/boost`: Filters the "Confirmed" sheet to show only signals
  matching that specific strategy.

---

## Troubleshooting

- Ensure your Google Service Account has Editor access to the target Google
  Sheet.
- Double-check your credentials and environment variables for typos.
- Review logs in the `logs/` directory for detailed error messages.

---

## License

MIT License
