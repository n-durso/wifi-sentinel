import threading
import time
import requests
import os
import psycopg2

class BotListener(threading.Thread):
    def __init__(self):
        super().__init__()
        self.token = os.getenv("TELEGRAM_TOKEN")
        self.base_url = f"https://api.telegram.org/bot{self.token}"
        self.running = True
        self.last_update_id = 0

    def get_db_connection(self):
        try:
            return psycopg2.connect(
                host=os.getenv("DB_HOST"),
                database=os.getenv("DB_NAME"),
                user=os.getenv("DB_USER"),
                password=os.getenv("DB_PASSWORD"),
                port=int(os.getenv("DB_PORT", 5432))
            )
        except Exception as e:
            print(f"[BOT] Errore connessione DB: {e}")
            return None

    def process_message(self, chat_id, text):
        # Cerca comandi che contengano "/start codice_segreto"
        if text.startswith("/start") and len(text) > 7:
            token_received = text.split(" ")[1] # prende la parte dopo lo spazio
            
            conn = self.get_db_connection()
            if not conn: return

            try:
                cur = conn.cursor()
                # Cerca l'utente che ha questo token
                cur.execute("SELECT id, username FROM users WHERE verification_token = %s", (token_received,))
                user = cur.fetchone()

                if user:
                    user_id, username = user
                    # Salva il Chat ID e cancella il token che è usa e getta
                    cur.execute(
                        "UPDATE users SET telegram_chat_id = %s, verification_token = NULL WHERE id = %s",
                        (str(chat_id), user_id)
                    )
                    conn.commit()
                    self.send_reply(chat_id, f" *Perfetto {username}!* \nTelegram collegato con successo.\nRiceverai qui gli allarmi.")
                    print(f"[BOT] Utente {username} collegato a ChatID {chat_id}")
                else:
                    self.send_reply(chat_id, " *Errore:* Token non valido o scaduto.\nRiprova dalla Dashboard.")
                
                cur.close()
                conn.close()
            except Exception as e:
                print(f"[BOT] Errore SQL: {e}")
        
        elif text == "/start":
            self.send_reply(chat_id, "Ciao! Per collegare le notifiche, usa il tasto 'Collega Telegram' dalla Dashboard web.")

    def send_reply(self, chat_id, text):
        try:
            url = f"{self.base_url}/sendMessage"
            requests.post(url, json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"})
        except Exception as e:
            print(f"[BOT] Errore invio: {e}")

    def run(self):
        print("[BOT] In ascolto di nuovi utenti...")
        while self.running:
            try:
                # aspetta 30 secondi se non ci sono messaggi
                url = f"{self.base_url}/getUpdates?offset={self.last_update_id + 1}&timeout=30"
                response = requests.get(url, timeout=35)
                
                if response.status_code == 200:
                    data = response.json()
                    for result in data.get("result", []):
                        self.last_update_id = result["update_id"]
                        if "message" in result:
                            chat_id = result["message"]["chat"]["id"]
                            text = result["message"].get("text", "")
                            self.process_message(chat_id, text)
                
                time.sleep(1) # pausa per evitare spam
            
            except Exception as e:
                print(f"[BOT] Errore loop: {e}")
                time.sleep(5)