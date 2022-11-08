import requests
import json, yaml
import logging
from packaging.version import Version, InvalidVersion

log = logging.getLogger('main')

class DockerService:
    def __init__(self, stack, service, image, conf, mqtt_client=None, version=None) -> None:
        url = image.split(':')[0]

        if version is None:
            version = image.split(':')[1] if ':' in image else None

        package = url.split('/')[-1]
        organisation = url.split('/')[-2] if len(url.split('/')) > 1 else 'library'
        repository = url.split('/')[0] if len(url.split('/')) == 3 else 'dockerhub'
    
        self.name = service
        self.stack = stack
        self.package = package
        self.url = url
        self.organisation = organisation
        self.repository = repository
        self.conf = conf
        self.mqtt_client = mqtt_client
        self.mqtt_service_topic = f"{self.conf.mqtt.topic}/{self.stack}/{self.name}/info"

        try:
            self.version = Version(version)
        except (InvalidVersion, TypeError):
            self.version = Version("0.0.0")

        self.latest_available_version = None
        self.available_tags = None
        self.set_uptodate(True)

    def get_availableimages(self):
        if self.repository == 'dockerhub':
            self.get_dockerhub_images()
        elif self.repository == 'lscr.io':
            self.get_linuxserver_images()
        elif self.repository == 'ghcr.io':
            self.get_github_images()
        else:
            raise NotImplementedError(f"Unknown repository {self.repository}")

        self.get_validversions()
        self.latest_available_version = self.get_latestversion()

    def get_dockerhub_images(self):
        with requests.get(f"https://hub.docker.com/v2/repositories/{self.organisation}/{self.package}/tags?status=active&page_size=100") as r:
            if r.ok:
                results = json.loads(r.text)["results"]
                tags = [result["name"] for result in results]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")
        self.available_tags = tags

    def get_linuxserver_images(self):
        with requests.get("https://fleet.linuxserver.io/api/v1/images") as r:
            if r.ok:
                results = json.loads(r.text)["data"]["repositories"]["linuxserver"]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.package}. Reason: {r.reason}")
        for result in results:
            if result["name"] == self.package:
                self.available_tags = [result["version"]]
                break
        if self.available_tags is None:
            raise ValueError(f"Could not find image {self.url} in LinuxServer.io")

    def get_github_images(self):
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

    def extract_versionnumber(self, version_number, alldigits=True):
        try:
            version = Version(version_number)
            return version
        except InvalidVersion:
            return None

    def get_validversions(self):
        if self.available_tags is None:
            log.warning(f"No available tags for {self.organisation}/{self.package}.")
        else:
            processed_versions = [self.extract_versionnumber(image_version) for image_version in self.available_tags]
            self.availableVersions = [Version(key) for key, val in zip(self.available_tags, processed_versions) if val is not None]

    def get_latestversion(self, branch='release'):
        images = self.availableVersions
        if branch == 'release':
            images = [image for image in images if not image.is_devrelease and not image.is_postrelease and not image.is_prerelease]
        else:
            raise NotImplementedError
        images.sort(reverse=True)
        return images[0]

    def update_check(self):
        if self.latest_available_version is None:
            self.get_availableimages()

        if self.latest_available_version > self.version:
            self.set_uptodate(False)
        else:
            self.set_uptodate(True)

    def set_version(self, version):
        self.version = version
        
        if self.conf.mqtt.enabled:
            payload = {
                "installed_version": str(self.version),
            }
            self.mqtt_client.publish(self.mqtt_service_topic, payload=yaml.dump(payload))

    def set_uptodate(self, uptodate):
        self.uptodate = uptodate
        
        if self.conf.mqtt.enabled:
            payload = {
                "installed_version": str(self.version),
                "latest_version": str(self.latest_available_version),
            }

            self.mqtt_client.publish(self.mqtt_service_topic, payload=json.dumps(payload))
