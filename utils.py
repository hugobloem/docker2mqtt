import logging
import json

log = logging.getLogger('main')

# empty class
class DctClass:
    def __init__(self, conf):
        for k, v in conf.items():
            if isinstance(v, dict):
                setattr(self, k, DctClass(v))
            else:
                setattr(self, k, v)

    def update(self, conf):
        for k, v in conf.items():
            if isinstance(v, dict):
                if not hasattr(self, k):
                    setattr(self, k, DctClass(v))
                else:
                    getattr(self, k).update(v)
            else:
                setattr(self, k, v)

# HomeAssistant utilities
def publish_ha_stack(stack, client, discovery_topic="homeassistant", grouping_device=None):
    '''
    Publish stack to HomeAssistant MQTT discovery topic
    '''
    device = {
        "name": stack.name if grouping_device is None else grouping_device,
        "identifiers": [stack.name if grouping_device is None else grouping_device],
    }

    # Update entity
    for service in stack.services:
        service_topic = f"{stack.mqtt_stack_topic}/{service}"
        payload = {
            "device": device,
            "name": f"{stack.name}/{service}",
            "availability": [
                # {"topic": f"{service_topic}/availability"},
                {"topic": f"{stack.conf.mqtt.topic}/availability"},
            ],
            "state_topic": f"{service_topic}/info",
            "unique_id": f"{stack.name}_{service}",
            "command_topic": f"{stack.mqtt_stack_topic}/command",
            "device_class": "firmware",
            "payload_install": json.dumps({"service": service, "update_stack": True, "deploy": True}),
        }
        client.publish(f"{discovery_topic}/update/{stack.name}/{service}/config", json.dumps(payload))