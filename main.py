import logging
import os
import paho.mqtt.client as mqtt

from DockerStack import DockerStack
import utils
import time
import yaml

conf_dct = {
    "input_dir": "/stacks",
    "log_level": "INFO",
    "github_token": None,

    "mqtt": {
        "enabled": True,
        "host": None,
        "port": 1883,
        "topic": "docker2mqtt",
    },

    "homeassistant": {
        "enabled": True,
        "discovery_prefix": "homeassistant",
        "grouping_device": None,
    },
}
conf = utils.DctClass(conf_dct)
conf.update(yaml.safe_load(open("/configuration.yaml", "r")))

# initialise logging
log = logging.getLogger('main')
log.setLevel(getattr(logging, conf.log_level))
log.addHandler(logging.StreamHandler())
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

    client.connect("rpi0.local", 1883, 60)
    client.loop_start()
    client.publish(f"{conf.mqtt.topic}/availability", "online", retain=True)

# Initialise stacks
for stack_file in stack_files:
    stack = DockerStack(stack_file.split('.')[0], input_dir + stack_file, conf, client if conf.mqtt else None)
    stack.get_services()
    stack.update_check('all')

    if conf.homeassistant.enabled:
        utils.publish_ha_stack(
            stack=stack,
            client=client if conf.mqtt.enabled else None,
            discovery_prefix=conf.homeassistant.discovery_prefix,
            grouping_device=conf.homeassistant.grouping_device,
        )

#     stack.updateCheck()
#     for service in stack.updateable:
#         log.info(f"Updating {service}...")
#         stack.updatestack_file(service)

    # stack.pushToDocker()

# Start a forever loop
while True:
    time.sleep(1)