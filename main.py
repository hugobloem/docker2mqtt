import logging
import os
from DockerStack import DockerStack
from argparse import ArgumentParser

parser = ArgumentParser()
parser.add_argument("-i", "--stacksDir", help="Directory containing stack files", required=True)
parser.add_argument("-l", "--logLevel", help="Log level", default="INFO")
parser.add_argument("--githubToken", help="Github token", default=os.environ.get("GITHUB_TOKEN"))

conf = parser.parse_args()

log = logging.getLogger('main')
log.setLevel(getattr(logging, conf.logLevel))
log.addHandler(logging.StreamHandler())
log.info("Starting")

stacksDir = "./stacks-copy/"
stackFiles = [f for f in os.listdir(stacksDir) if f.endswith(".yml") or f.endswith(".yaml")]

for stackFile in stackFiles:
    stack = DockerStack(stackFile.split('.')[0], stacksDir + stackFile, conf)
    stack.getServices()

    stack.updateCheck()
    for service in stack.updateable:
        log.info(f"Updating {service}...")
        stack.updateStackFile(service)

    # stack.pushToDocker()