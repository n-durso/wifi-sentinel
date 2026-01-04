import paho.mqtt.client as mqtt
import json
import os
from evaluator import Evaluator
from db import save_snapshot
from notifier import TelegramNotifier

broker_host = os.getenv("MQTT_HOST", "127.0.0.1")
broker_port = int(os.getenv("MQTT_PORT", 1883))

class EventSubscriber:
    def __init__(self, evaluator, broker=broker_host, port=broker_port, topic="wifi/events"):
        self.evaluator = evaluator
        self.notifier = TelegramNotifier()
        self.topic = topic
        self.client = mqtt.Client(client_id="sentinel-core")
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message
        self.client.connect(broker, port)
        self.client.subscribe(topic)

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print("[MQTT] Connesso. Iscrizione al topic...")
            client.subscribe(self.topic)
        else:
            print("[MQTT] ERRORE:", rc)


    def on_message(self, client, userdata, msg):
        try:
            # Decodifica JSON ricevuto dal Monitor
            event = json.loads(msg.payload.decode())
            # Estraggo la lista delle reti (che serve all'Evaluator)
            networks = event.get("networks", [])
            timestamp = event.get("timestamp")
        except Exception as e:
            print("[CORE] Errore parsing JSON:", e)
            return

        # Analisi
        status, score, details = self.evaluator.analyze(networks)

        # Salvataggio DB
        try:
            save_snapshot(timestamp, json.dumps(networks), status, score, details or "")
        except Exception as e:
            print("[DB] Errore salvataggio:", e)

        

        # --- OUTPUT e TELEGRAM---
        if status == "SAFE":
            # Output minimale se SAFE
            count = len(event.get("networks", []))
            print(f"[CORE] ✅ SAFE - Analizzate {count} reti (Score: {score:.1f})")
        
        else:
            # Output più corposo se SUSPICIOUS o EVIL_TWIN
            color = "⚠️" if status == "SUSPICIOUS" else "🚨"
            border = "!" * 60
            
            print("\n" + border)
            print(f"{color}  {status} DETECTED (Score: {score:.2f})  {color}")
            print("-" * 60)
            
            if details:
                print(f" -> {details}")
            else:
                print(" -> Nessun dettaglio specifico.")
            
            print(border + "\n")

            # Notifica Telegram solo per EVIL_TWIN
            if status == "EVIL_TWIN":
                # Usiamo 'details' anche nel messaggio Telegram per coerenza
                msg_text = (
                    f"🚨 *ALLARME WIFI SENTINEL* 🚨\n\n"
                    f"⚠️ *Rilevato Attacco EVIL TWIN*\n"
                    f"📉 *Score:* {score:.2f}\n\n"
                    f"🔍 *Dettagli:*\n{details}"
                )
                self.notifier.send_alert(msg_text)

    def start(self):
        print("[SUBSCRIBER] in ascolto...")
        self.client.loop_forever()


if __name__ == "__main__":
    evaluator = Evaluator()
    subscriber = EventSubscriber(evaluator)
    subscriber.start()