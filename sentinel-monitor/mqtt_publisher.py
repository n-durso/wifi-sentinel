import paho.mqtt.client as mqtt
import json
import os

broker_host = os.getenv("MQTT_HOST", "127.0.0.1")
broker_port = int(os.getenv("MQTT_PORT", 1883))

class MqttPublisher:
    def __init__(self, broker_host=broker_host, broker_port=broker_port, topic="wifi/events"):
        self.client = mqtt.Client()

        # Avvia il loop della rete
        self.client.loop_start() # Non blocca l'esecuzione

        # Connessione al broker
        self.client.connect(broker_host, broker_port)

        self.topic = topic

    def publish_event(self, event: dict):
        payload = json.dumps(event)
        self.client.publish(self.topic, payload)
        print(f"[MQTT] Evento pubblicato → {payload}")
