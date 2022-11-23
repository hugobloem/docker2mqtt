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
        available_tags = None
        with requests.get(
                url=f"https://api.github.com/orgs/{self.organisation}/packages/container/{self.package}/versions", 
                headers={"Accept": "application/vnd.github+json", "Authorization": f"token {self.conf.general.github_token}"},
            ) as r:
            if r.ok:
                results = r.json()
            for result in results:
                tag = result["metadata"]["container"]["tags"]
                if len(tag):
                    if available_tags is None:
                        available_tags = [tag[0]]
                    else:
                        available_tags += [tag[0]]
                else:
                    log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")

        return available_tags