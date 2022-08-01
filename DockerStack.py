import os
import yaml
import docker
import logging

from DockerService import DockerService

log = logging.getLogger('main')

class DockerStack:
    def __init__(self, name, stackFile, conf) -> None:
        super().__init__()
        
        self.name = name
        self.stackFile = stackFile
        self.conf = conf
        self.readStack()
        self.upToDate = {}

    def readStack(self):
        log.debug(f"Reading stack file {self.stackFile}")
        with open(self.stackFile, 'r') as f:
            self.stack = yaml.safe_load(f)
    
    def writeStack(self):
        log.debug(f"Writing stack file {self.stackFile}")
        with open(self.stackFile, 'w') as f:
            yaml.safe_dump(self.stack, f)
    
    def getServices(self):
        services = {}
        for service, val in self.stack["services"].items():
            labels = self.extractLabels(val)
            if labels["enable"]:
                services[service] = DockerService(val["image"], self.conf)

        self.services = services
        log.debug(f"Found services: {list(self.services.keys())}")

    def updateCheck(self):
        for name, service in self.services.items():
            service.updateCheck()
            self.upToDate[name] = service.upToDate
        self.updateable = [k for k, v in self.upToDate.items() if not v]
        log.debug(f"Updateable services: {self.updateable}")

    def updateStackFile(self, service):
        newImage = f"{self.services[service].url}:{self.services[service].latestAvailableVersion}"
        self.stack["services"][service]["image"] = newImage
        self.writeStack()
        log.info(f"Updated {service} to {newImage}")

    def pushToDocker(self):
        os.system(f"docker stack deploy -c {self.stackFile} {self.name}")

    def extractLabels(self, config):
        labels = {
            "enable": True,
        }

        if "labels" in config:
            confLabels = config["labels"]
            for label in confLabels:
                if label.startswith("docker2mqtt."):
                    labels[label.split("=")[0].replace("docker2mqtt.", "")] = eval(label.split("=")[1])
        
        return labels