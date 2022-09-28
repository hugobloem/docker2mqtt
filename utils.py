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

# MQTT utilities
def on_connect(client, userdata, flags, rc):
    log.info("MQTT connected with result code "+str(rc))


def on_message(client, userdata, msg):
    log.info(msg.topic+" "+str(msg.payload))

# HomeAssistant utilities
def publish_ha_stack(stack, client, discovery_prefix="homeassistant", grouping_device=None):
    '''
    Publish stack to HomeAssistant MQTT discovery topic
    '''
    device = {
        "name": stack.name,
        "identifiers": [stack.name if grouping_device is None else grouping_device],
    }

    # Update stack switch
    client.publish(f"{discovery_prefix}/switch/{stack.name}/config", json.dumps({
        "device": device,
        "availability": [
            {"topic": f"{stack.mqtt_stack_topic}/availability"},
            {"topic": f"{stack.conf.mqtt.topic}/availability"},
        ],
        "availability_mode": "all",
        "name": f"{stack.name} up to date",
        "state_topic": f"{stack.mqtt_stack_topic}/up_to_date",
        "value_template": "{{ value_json.state }}",
        "unique_id": f"{stack.name}_uptodate",
        "command_topic": f"{stack.mqtt_stack_topic}/update",
    }
    ))

    # Updatea services switch
    for service in stack.services:
        client.publish(f"{discovery_prefix}/binary_sensor/{stack.name}/{service}/config", json.dumps({
            "device": device,
            "name": f"{stack.name}/{service} updateable",
            "state_topic": f"{stack.mqtt_stack_topic}/services/{service}",
            "unique_id": f"{stack.name}_{service}_uptodate",
        }))
    