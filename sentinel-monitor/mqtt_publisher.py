import paho.mqtt.client as mqtt
import json

class MqttPublisher:
    def __init__(self, broker_host="broker", broker_port=1883, topic="wifi/events"):
        self.client = mqtt.Client()
        self.client.connect(broker_host, broker_port)
        self.topic = topic

    def publish_event(self, event: dict):
        payload = json.dumps(event)
        self.client.publish(self.topic, payload)
        print(f"[MQTT] Evento pubblicato → {payload}")
