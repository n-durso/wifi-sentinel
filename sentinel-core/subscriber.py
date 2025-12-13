import paho.mqtt.client as mqtt
import json
import os
from evaluator import Evaluator

broker_host = os.getenv("MQTT_HOST", "127.0.0.1")
broker_port = int(os.getenv("MQTT_PORT", 1883))

class EventSubscriber:
    def __init__(self, evaluator, broker=broker_host, port=broker_port, topic="wifi/events"):
        self.evaluator = evaluator
        self.topic = topic
        self.client = mqtt.Client(client_id="sentinel-core")
        self.client.on_message = self.on_message
        self.client.connect(broker, port)
        self.client.subscribe(topic)


    def on_message(self, client, userdata, msg):
        event = json.loads(msg.payload.decode())
        print("Evento ricevuto:", event)

        decision = self.evaluator.evaluate_event(event)
        print("[CORE] Decision: ", decision)

    def start(self):
        print("[SUBSCRIBER] in ascolto...")
        self.client.loop_forever()


if __name__ == "__main__":
    evaluator = Evaluator()
    subscriber = EventSubscriber(evaluator)
    subscriber.start()