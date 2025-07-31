import os
import time
import requests
from telegram_bot import handle_clear_command, send_telegram_message

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

#Clear commands
def poll_for_commands():
    print("[TelegramBotRunner] Polling for commands...")
    last_update_id = None
    while True:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"
        params = {"timeout": 30}
        if last_update_id:
            params["offset"] = last_update_id + 1
        try:
            resp = requests.get(url, params=params, timeout=35)
            if not resp.ok:
                print("[TelegramBotRunner] Failed to get updates.")
                time.sleep(10)
                continue
            updates = resp.json().get("result", [])
            for update in updates:
                last_update_id = update["update_id"]
                message = update.get("message")
                if not message:
                    continue
                text = message.get("text", "")
                user_id = message["from"]["id"]
                if text.strip() == "/clear":
                    send_telegram_message("Cleared all meassages")
                    handle_clear_command()
        except Exception as e:
            print(f"[TelegramBotRunner] Error: {e}")
        time.sleep(5)

if __name__ == "__main__":
    poll_for_commands()
