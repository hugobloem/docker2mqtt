import os
import yaml
import logging
import json

from DockerService import DockerService

log = logging.getLogger('main')

class DockerStack:
    def __init__(self, name, stackFile, conf, mqttClient=None) -> None:
        super().__init__()
        
        self.name = name
        self.stackFile = stackFile
        self.conf = conf
        self.readStack()
        self.upToDate = {}

        if conf.mqtt:
            # Subscribe to MQTT topic
            self.mqttClient = mqttClient
            self.mqttStackTopic = f"docker2mqtt/{self.name}"
            self.mqttClient.subscribe(f"{self.mqttStackTopic}/#")
            log.debug(f"MQTT subscribe to '{self.mqttStackTopic}/#'")

            # Add callbacks
            self.mqttClient.message_callback_add(f'{self.mqttStackTopic}/update', self.update_handler)
            self.mqttClient.message_callback_add(f'{self.mqttStackTopic}/info', self.info_handler)


    def readStack(self):
        '''
        Read a stack file.
        '''
        log.debug(f"Reading stack file {self.stackFile}")
        with open(self.stackFile, 'r') as f:
            self.stack = yaml.safe_load(f)
    

    def writeStack(self):
        '''
        Write a stack file.
        '''
        log.debug(f"Writing stack file {self.stackFile}")
        with open(self.stackFile, 'w') as f:
            yaml.safe_dump(self.stack, f)
    

    def getServices(self):
        '''
        Get services from the stack file.
        '''
        services = {}
        for service, val in self.stack["services"].items():
            labels = self.extractLabels(val)
            if labels["enable"]:
                services[service] = DockerService(self.name, val["image"], self.conf, self.mqttClient)

        self.services = services
        log.debug(f"Found services: {list(self.services.keys())}")


    def updateCheck(self):
        '''
        Check whether newer images are available.
        '''
        for name, service in self.services.items():
            service.updateCheck()
            self.upToDate[name] = service.upToDate
        self.updateable = [k for k, v in self.upToDate.items() if not v]
        log.debug(f"Updateable services: {self.updateable}")


    def updateStackFile(self, service):
        '''
        Update the stack file to the newer images.
        '''
        newImage = f"{self.services[service].url}:{self.services[service].latestAvailableVersion}"
        self.stack["services"][service]["image"] = newImage
        self.writeStack()
        log.info(f"Updated {service} to {newImage}")


    def deployToDocker(self):
        '''
        Deploy the docker stack and set service to be up to date.
        '''
        os.system(f"docker stack deploy -c {self.stackFile} {self.name}")
        for service in self.updateable:
            self.services[service].setUpToDate(True)


    def extractLabels(self, config):
        '''
        Extract labels from the docker services
        '''
        labels = {
            "enable": True,
        }

        if "labels" in config:
            confLabels = config["labels"]
            for label in confLabels:
                if label.startswith("docker2mqtt."):
                    labels[label.split("=")[0].replace("docker2mqtt.", "")] = eval(label.split("=")[1])
        
        return labels


    def update_handler(self, client, userdata, message):
        '''
        Handle update messages.
        '''

        payload = {
            "service": "all",
            "update_stack": False,
            "deploy": False,
        }

        topic = message.topic
        try:
            payload.update(json.loads(message.payload.decode("utf-8")))
        except:
            log.warning(f"Could not decode payload for topic {topic}\n{message.payload}")
            return

        log.debug(f"MQTT message received: {topic} {message.payload}")

        assert topic.startswith(self.mqttStackTopic)

        if payload["deploy"]:
            payload["update_stack"] = True

        if topic == f"{self.mqttStackTopic}/update":
            self.updateCheck()

            if payload["update_stack"]:

                if payload["service"] == "all":
                    for service in self.updateable:
                        self.updateStackFile(service)
                else:
                    self.updateStackFile(payload["service"])

            if payload["deploy"]:
                self.deployToDocker()

    
    def info_handler(self, client, userdata, message):
        '''
        Handle info messages.
        '''
        payload = {
            "service": "all",
        }

        topic = message.topic
        try:
            payload.update(json.loads(message.payload.decode("utf-8")))
        except:
            log.warning(f"Could not decode payload for topic {topic}\n{message.payload}")
            return

        log.debug(f"MQTT message received: {topic} {message.payload}")

        assert topic.startswith(self.mqttStackTopic)

        if topic == f"{self.mqttStackTopic}/info":
            if payload["service"] == "all":
                for service in self.services:
                    log.info(f"Sending info for {service}")
            else:
                log.info(f"Sending info for {payload['service']}")