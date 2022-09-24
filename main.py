import logging
import os
from argparse import ArgumentParser
import paho.mqtt.client as mqtt

from DockerStack import DockerStack
import utils
import time

parser = ArgumentParser()
parser.add_argument("-i", "--stacksDir", help="Directory containing stack files", required=True)
parser.add_argument("-l", "--logLevel", help="Log level", default="INFO")
parser.add_argument("--githubToken", help="Github token", default=os.environ.get("GITHUB_TOKEN"))
parser.add_argument("--no-mqtt", help="Disable MQTT", action="store_true")
parser.add_argument("--mqtt-topic", help="MQTT topic", default="docker2mqtt")

conf = utils.EmptyClass(parser.parse_args())

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

# Initialise stacks
for stackFile in stackFiles:
    stack = DockerStack(stackFile.split('.')[0], stacksDir + stackFile, conf, client if conf.mqtt else None)
    stack.getServices()

#     stack.updateCheck()
#     for service in stack.updateable:
#         log.info(f"Updating {service}...")
#         stack.updateStackFile(service)

    # stack.pushToDocker()

# Start a forever loop
while True:
    time.sleep(1)