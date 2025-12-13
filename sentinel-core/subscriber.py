import paho.mqtt.client as mqtt
import json

class EventSubscriber:
    def __init__(self, evaluator, broker="localhost", topic="wifi/events"):
        self.evaluator = evaluator
        self.topic = topic
        self.client = mqtt.Client(client_id="sentinel-core", callback_api_version=2)
        self.client.on_message = self.on_message
        self.client.connect(broker, 1883)
        self.client.subscribe(topic)


    def on_message(self, client, userdata, msg):
        event = json.loads(msg.payload.decode())
        print("Evento ricevuto:", event)

        decision = self.evaluator.evaluate_event(event)
        print("[CORE] Decision: ", decision)

    def start(self):
        print("[SUBSCRIBER] in ascolto...")
        self.client.loop_forever()