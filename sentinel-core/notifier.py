import requests
import os
import psycopg2

class TelegramNotifier:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_TOKEN")

    def get_recipients(self):
        # Scarica dal DB la lista di tutti gli utenti con telegram_chat_id non nullo
        recipients = []
        try:
            conn = psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=int(os.getenv("DB_PORT", 5432))
            )
            cur = conn.cursor()
            
            cur.execute("SELECT telegram_chat_id FROM users WHERE telegram_chat_id IS NOT NULL")
            rows = cur.fetchall()
            # Serve per trasformare 
            # da [('123',), ('456',)] a ['123', '456']
            recipients = [row[0] for row in rows if row[0]]
            
            cur.close()
            conn.close()
        except Exception as e:
            print(f"[NOTIFIER] ❌ Errore lettura destinatari: {e}")
        
        return recipients

    def send_alert(self, message):
        if not self.token:
            print("[NOTIFIER] Token mancante!")
            return

        # Trova a chi mandarlo
        chat_ids = self.get_recipients()
        
        if not chat_ids:
            print("[NOTIFIER] ⚠️ Nessun utente Telegram registrato. Nessuna notifica inviata.")
            return

        # Invia a tutti
        for chat_id in chat_ids:
            try:
                url = f"https://api.telegram.org/bot{self.token}/sendMessage"
                payload = {
                    "chat_id": chat_id,
                    "text": message
                }
                requests.post(url, json=payload, timeout=5)
            except Exception as e:
                print(f"[NOTIFIER] Errore invio a {chat_id}: {e}")
        
        print(f"[NOTIFIER] ✅ Allarme inviato a {len(chat_ids)} utenti.")