import logging
import os
import paho.mqtt.client as mqtt

from DockerStack import DockerStack
import utils
import time
import yaml

conf_dct = {
    "general": {
        "input_dir": "/stacks",
        "log_level": "INFO",
        "github_token": None,
        "sleep_time": 3600,
    },
    "mqtt": {
        "enabled": True,
        "host": None,
        "port": 1883,
        "topic": "docker2mqtt",
    },

    "homeassistant": {
        "enabled": True,
        "discovery_topic": "homeassistant",
        "grouping_device": None,
    },
}
conf = utils.DctClass(conf_dct)
conf.update(yaml.safe_load(open("/configuration.yaml", "r")))

# initialise logging
logging.basicConfig(
    level=conf.general.log_level,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%d/%m %H:%M:%S",)
log = logging.getLogger('main')
log.info("Starting")

# Find stack files
input_dir = "/stacks/"
stack_files = [f for f in os.listdir(input_dir) if f.endswith(".yml") or f.endswith(".yaml")]
log.info(f"Found {len(stack_files)} in {input_dir}")

# Setup mqtt client
if conf.mqtt.enabled:
    client = mqtt.Client()
    client.on_connect = utils.on_connect
    client.on_message = utils.on_message
    
    try:
        client.connect(conf.mqtt.host, conf.mqtt.port, 60)
    except Exception as e:
        log.error(f"Could not connect to {conf.mqtt.host}:{conf.mqtt.port} with error: {e}")
        exit

    client.loop_start()
    client.will_set(f"{conf.mqtt.topic}/availability", "offline")

# Initialise stacks
stacks = []
for stack_file in stack_files:
    stack = DockerStack(stack_file.split('.')[0], input_dir + stack_file, conf, client if conf.mqtt else None)
    stack.get_services()
    stacks.append(stack)

    if conf.homeassistant.enabled:
        utils.publish_ha_stack(
            stack=stack,
            client=client if conf.mqtt.enabled else None,
            discovery_topic=conf.homeassistant.discovery_topic,
            grouping_device=conf.homeassistant.grouping_device,
        )

# Start a forever loop
while True:
    for stack in stacks:
        stack.update_check('all')
    time.sleep(conf.general.sleep_time)
