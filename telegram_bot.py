import os
import requests


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# Track sent message IDs in a file
MESSAGE_ID_FILE = "bot_message_ids.txt"

def track_message_id(message_id):
    try:
        with open(MESSAGE_ID_FILE, "a") as f:
            f.write(str(message_id) + "\n")
    except Exception as e:
        print(f"[Telegram] Failed to track message id {message_id}: {e}")

def get_tracked_message_ids():
    try:
        with open(MESSAGE_ID_FILE, "r") as f:
            return [int(line.strip()) for line in f if line.strip()]
    except FileNotFoundError:
        return []
    except Exception as e:
        print(f"[Telegram] Failed to read tracked message ids: {e}")
        return []

def clear_tracked_message_ids():
    try:
        open(MESSAGE_ID_FILE, "w").close()
    except Exception as e:
        print(f"[Telegram] Failed to clear message id file: {e}")


def send_telegram_message(text):
    """Send a message to the configured Telegram chat."""
    if TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": text, "parse_mode": "HTML"}
        try:
            resp = requests.post(url, data=payload, timeout=10)
            if resp.ok:
                data = resp.json()
                message_id = data.get("result", {}).get("message_id")
                if message_id:
                    track_message_id(message_id)
            else:
                print(f"[Telegram Error] Failed to send message: {resp.text}")
        except Exception as e:
            print(f"[Telegram Error] {e}")
    else:
        print("[Telegram] Bot token or chat ID not set in environment.")

def handle_clear_command():
    """Deletes all messages in the chat if the user is an admin. To be called when /clear is received."""
    if not (TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID):
        print("[Telegram] Bot token or chat ID not set in environment.")
        return
    message_ids = get_tracked_message_ids()
    print(f"[Telegram] Tracked message IDs to delete: {message_ids}")
    for message_id in message_ids:
        del_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/deleteMessage"
        del_payload = {"chat_id": TELEGRAM_CHAT_ID, "message_id": message_id}
        try:
            resp = requests.post(del_url, data=del_payload, timeout=10)
            if not resp.ok:
                print(f"[Telegram] Failed to delete message {message_id}: {resp.text}")
        except Exception as e:
            print(f"[Telegram] Failed to delete message {message_id}: {e}")
    clear_tracked_message_ids()
