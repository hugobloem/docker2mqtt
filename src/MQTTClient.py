import logging
import paho.mqtt.client as mqtt

log = logging.getLogger('main')

class MQTTClient:
    def __init__(self, conf):
        self.conf = conf
        self.client = mqtt.Client()
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        try:
            self.connect()
        except Exception as e:
            log.error(f"Could not connect to {conf.host}:{conf.port} with error: {e}")
            exit

        self.client.loop_start()
        self.client.will_set(f"{self.conf.topic}/availability", "offline")


    def connect(self):
        self.client.connect(self.conf.host, self.conf.port, 60)

    def publish(self, topic, payload, *args, **kwargs):
        log.info(f"Publish to {topic}: {payload}")
        self.client.publish(topic, payload, *args, **kwargs)

    def subscribe(self, topic, *args, **kwargs):
        log.info(f"Subscribing to {topic}")
        self.client.subscribe(topic, *args, **kwargs)

    def message_callback_add(self, *args, **kwargs):
        self.client.message_callback_add(*args, **kwargs)


    def on_connect(self, client, userdata, flags, rc):
        log.info("MQTT connected with result code "+str(rc))
        client.publish(f"{self.conf.topic}/availability", "online", retain=True)

    def on_message(self, client, userdata, msg):
        log.info(f"Message received on {msg.topic}: {str(msg.payload)}")