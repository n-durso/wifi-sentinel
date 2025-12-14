import requests
import os

class TelegramNotifier:
    def __init__(self):
        # Legge le credenziali dalle variabili d'ambiente
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")

    def send_alert(self, message):
        if not self.token or not self.chat_id:
            print("[NOTIFIER] ⚠️ Token o Chat ID mancante. Notifica saltata.")
            return

        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "Markdown" # Permette il grassetto
        }

        try:
            response = requests.post(url, json=payload, timeout=5)
            if response.status_code == 200:
                print("[NOTIFIER] ✅ Messaggio Telegram inviato.")
            else:
                print(f"[NOTIFIER] ❌ Errore Telegram: {response.text}")
        except Exception as e:
            print(f"[NOTIFIER] ❌ Errore connessione Telegram: {e}")