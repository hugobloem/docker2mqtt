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
        "mqtt_host": None,
        "mqtt_port": 1883,
        "mqtt_topic": "docker2mqtt",
    },

    "homeassistant": {
        "discovery_prefix": "homeassistant",
        "grouping_device": None,
    },
}
conf_dct.update(yaml.safe_load(open("./configuration.yaml", "r")))
conf = utils.DctClass(conf_dct)

# initialise logging
log = logging.getLogger('main')
log.setLevel(getattr(logging, conf.logLevel))
log.addHandler(logging.StreamHandler())
log.info("Starting")

# Find stack files
stacksDir = "./stacks-copy/"
stackFiles = [f for f in os.listdir(stacksDir) if f.endswith(".yml") or f.endswith(".yaml")]
log.info(f"Found {len(stackFiles)} in {stacksDir}")

# Setup mqtt client
conf.mqtt = not conf.no_mqtt
if conf.mqtt:
    client = mqtt.Client()
    client.on_connect = utils.on_connect
    client.on_message = utils.on_message

    client.connect("rpi0.local", 1883, 60)
    client.loop_start()
    client.publish(f"{conf.mqtt_topic}/availability", "online", retain=True)

# Initialise stacks
for stackFile in stackFiles:
    stack = DockerStack(stackFile.split('.')[0], stacksDir + stackFile, conf, client if conf.mqtt else None)
    stack.getServices()
    if conf.ha:
        utils.publishHAstack(stack, client if conf.mqtt else None, grouping_device=conf.grouping_device)

#     stack.updateCheck()
#     for service in stack.updateable:
#         log.info(f"Updating {service}...")
#         stack.updateStackFile(service)

    # stack.pushToDocker()

# Start a forever loop
while True:
    time.sleep(1)