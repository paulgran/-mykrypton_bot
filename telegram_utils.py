import requests
import config

def send_telegram_message(message):
    if config.ENABLE_TG:
        try:
            url = f"https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage"
            data = {
                "chat_id": config.CHAT_ID,
                "text": message
            }
            requests.post(url, data=data)
        except Exception as e:
            print("Telegram Error:", e)
