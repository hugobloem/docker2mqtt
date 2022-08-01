import logging
import os
from DockerStack import DockerStack

log = logging.getLogger('main')
log.setLevel(logging.DEBUG)
log.addHandler(logging.StreamHandler())
log.info("Starting")

stacksDir = "./stacks-copy/"
stackFiles = [f for f in os.listdir(stacksDir) if f.endswith(".yml") or f.endswith(".yaml")]

for stackFile in stackFiles:
    stack = DockerStack(stackFile.split('.')[0], stacksDir + stackFile)
    stack.getServices()

    stack.updateCheck()
    for service in stack.updateable:
        log.info(f"Updating {service}...")
        stack.updateStackFile(service)

    # stack.pushToDocker()