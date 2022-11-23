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
        with requests.get(
                url=f"https://api.github.com/orgs/{self.organisation}/packages/container/{self.package}/versions", 
                headers={"Accept": "application/vnd.github+json", "Authorization": f"token {self.conf.github_token}"},
            ) as r:
            if r.ok:
                results = r.json()
            for result in results:
                tag = result["metadata"]["container"]["tags"]
                if len(tag):
                    if self.available_tags is None:
                        self.available_tags = [tag[0]]
                    else:
                        self.available_tags += [tag[0]]
                else:
                    log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")