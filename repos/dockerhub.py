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
        with requests.get(f"https://hub.docker.com/v2/repositories/{self.organisation}/{self.package}/tags?status=active&page_size=100") as r:
            if r.ok:
                results = json.loads(r.text)["results"]
                tags = [result["name"] for result in results]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")
        
        return tags