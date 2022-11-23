import requests
import json
import logging

log = logging.getLogger('main')

class Repository:
    def __init__(self, organisation, package, conf) -> None:
        self.organisation = organisation
        self.package = package
        self.conf = conf

    def get_images(self):
        with requests.get("https://fleet.linuxserver.io/api/v1/images") as r:
            if r.ok:
                results = json.loads(r.text)["data"]["repositories"]["linuxserver"]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")
                
        for result in results:
            if result["name"] == self.package:
                available_tags = [result["version"]]
                break
        if available_tags is None:
            raise ValueError(f"Could not find image {self.url} in LinuxServer.io")

        return available_tags