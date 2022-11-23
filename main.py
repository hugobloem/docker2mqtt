import logging
import os


from src.DockerStack import DockerStack
from src.MQTTClient import MQTTClient
import utils
import time
import yaml

# Load configuration
conf = utils.DctClass(yaml.safe_load(open('defaults.yaml', 'r')))
conf.update(yaml.safe_load(open("/configuration.yaml", "r")))

# initialise logging
logging.basicConfig(
    level=conf.general.log_level,
    format="[%(asctime)s] %(levelname)s  %(message)s",
    datefmt="%d/%m %H:%M:%S",)
log = logging.getLogger('main')
log.info("Starting")

# Find stack files
input_dir = conf.general.input_dir
stack_files = [f for f in os.listdir(input_dir) if f.endswith(".yml") or f.endswith(".yaml")]
log.info(f"Found {len(stack_files)} in {input_dir}")

# Setup mqtt client
if conf.mqtt.enabled:
    client = MQTTClient(conf.mqtt)

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
