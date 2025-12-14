import paho.mqtt.client as mqtt
import json
import os
from evaluator import Evaluator
from db import save_snapshot

broker_host = os.getenv("MQTT_HOST", "127.0.0.1")
broker_port = int(os.getenv("MQTT_PORT", 1883))

class EventSubscriber:
    def __init__(self, evaluator, broker=broker_host, port=broker_port, topic="wifi/events"):
        self.evaluator = evaluator
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
            event = json.loads(msg.payload.decode())
        except Exception as e:
            print("[CORE] Errore parsing JSON:", e)
            return

        # Salvataggio DB
        try:
            save_snapshot(event["timestamp"], json.dumps(event["networks"]))
        except Exception as e:
            print("[DB] Errore salvataggio:", e)

        # Analisi
        decision = self.evaluator.evaluate_event(event)
        
        status = decision["status"]
        score = decision["score"]
        reasons = decision["reasons"]

        # --- OUTPUT ---
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
            
            if not reasons:
                print("Nessun motivo specifico fornito (controllare logica strategie).")
            else:
                for reason in reasons:
                    print(f" -> {reason}")
            
            print(border + "\n")

    def start(self):
        print("[SUBSCRIBER] in ascolto...")
        self.client.loop_forever()


if __name__ == "__main__":
    evaluator = Evaluator()
    subscriber = EventSubscriber(evaluator)
    subscriber.start()