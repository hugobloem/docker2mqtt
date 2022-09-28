import os
import yaml
import logging
import json

from DockerService import DockerService

log = logging.getLogger('main')

class DockerStack:
    def __init__(self, name, stack_file, conf, mqtt_client=None) -> None:
        super().__init__()
        
        self.name = name
        self.stack_file = stack_file
        self.conf = conf
        self.read_stack()
        self.uptodate = {}

        if conf.mqtt.enabled:
            # Subscribe to MQTT topic
            self.mqtt_client = mqtt_client
            self.mqtt_stack_topic = f"docker2mqtt/{self.name}"
            self.mqtt_client.subscribe(f"{self.mqtt_stack_topic}/#")
            log.debug(f"MQTT subscribe to '{self.mqtt_stack_topic}/#'")

            # Add callbacks
            self.mqtt_client.message_callback_add(f'{self.mqtt_stack_topic}/update', self.update_handler)
            self.mqtt_client.message_callback_add(f'{self.mqtt_stack_topic}/info', self.info_handler)

            # Publish availability
            self.mqtt_client.publish(f"{self.mqtt_stack_topic}/availability", "online", retain=True)


    def read_stack(self):
        '''
        Read a stack file.
        '''
        log.debug(f"Reading stack file {self.stack_file}")
        with open(self.stack_file, 'r') as f:
            self.stack = yaml.safe_load(f)
    

    def write_stack(self):
        '''
        Write a stack file.
        '''
        log.debug(f"Writing stack file {self.stack_file}")
        with open(self.stack_file, 'w') as f:
            yaml.safe_dump(self.stack, f)
    

    def get_services(self):
        '''
        Get services from the stack file.
        '''
        services = {}
        for service, val in self.stack["services"].items():
            labels = self.extract_labels(val)
            if labels["enable"]:
                services[service] = DockerService(self.name, service, val["image"], self.conf, self.mqtt_client)

        self.services = services
        log.debug(f"Found services: {list(self.services.keys())}")


    def update_check(self, service_name="all"):
        '''
        Check whether newer images are available.
        '''
        if service_name == "all":
            for name, service in self.services.items():
                service.update_check()
                self.uptodate[name] = service.uptodate
            self.updateable = [k for k, v in self.uptodate.items() if not v]
        else:
            self.services[service_name].update_check()
            self.uptodate[service_name] = self.services[service_name].uptodate
            self.updateable = [k for k, v in self.uptodate.items() if not v]
        if any(self.updateable):
            self.mqtt_client.publish(f"{self.mqtt_stack_topic}/up_to_date", json.dumps({"state": "ON"}))
            log.debug(f"Updateable services: {self.updateable}")
        else:
            self.mqtt_client.publish(f"{self.mqtt_stack_topic}/up_to_date", json.dumps({"state": "OFF"}))
            log.debug("No updateable services")

    def update_stackfile(self, service):
        '''
        Update the stack file to the newer images.
        '''
        new_image = f"{self.services[service].url}:{self.services[service].latest_available_version}"
        self.stack["services"][service]["image"] = new_image
        self.write_stack()
        log.info(f"Updated {service} to {new_image}")


    def deploy_to_docker(self):
        '''
        Deploy the docker stack and set service to be up to date.
        '''
        os.system(f"docker stack deploy -c {self.stack_file} {self.name}")
        for service in self.updateable:
            self.services[service].setUpToDate(True)


    def extract_labels(self, config):
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

        assert topic.startswith(self.mqtt_stack_topic)
        if payload["service"] != "all":
            if payload["service"] not in self.services.keys():
                log.warning(f"Service {payload['service']} not found in stack {self.name}\nChoose from {list(self.services.keys())}")
                return

        if payload["deploy"]:
            payload["update_stack"] = True

        if topic == f"{self.mqtt_stack_topic}/update":

            self.update_check(payload["service"])

            if payload["update_stack"]:

                if payload["service"] == "all":
                    for service in self.updateable:
                        self.update_stackfile(service)
                else:
                    self.update_stackfile(payload["service"])

            if payload["deploy"]:
                self.deploy_to_docker()

    
    def info_handler(self, client, userdata, message):
        '''
        Handle info messages. TODO: send meaningful information
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

        assert topic.startswith(self.mqtt_stack_topic)

        if topic == f"{self.mqtt_stack_topic}/info":
            if payload["service"] == "all":
                for service in self.services:
                    log.info(f"Sending info for {service}")
            else:
                log.info(f"Sending info for {payload['service']}")