import requests
import json, yaml
import logging
from packaging.version import Version, InvalidVersion

log = logging.getLogger('main')

class DockerService:
    def __init__(self, stack, image, conf, mqttClient=None, version=None) -> None:
        url = image.split(':')[0]

        if version is None:
            version = image.split(':')[1] if ':' in image else None

        name = url.split('/')[-1]
        organisation = url.split('/')[-2] if len(url.split('/')) > 1 else 'library'
        repository = url.split('/')[0] if len(url.split('/')) == 3 else 'dockerhub'
    
        self.stack = stack
        self.name = name
        self.url = url
        self.organisation = organisation
        self.repository = repository
        self.conf = conf
        self.mqttClient = mqttClient
        self.mqttServiceTopic = f"{self.conf.mqtt_topic}/{self.stack}/{self.name}"

        try:
            self.version = Version(version)
        except (InvalidVersion, TypeError):
            self.version = Version("0.0.0")

        self.setUpToDate(True)
        self.latestAvailableVersion = None
        self.availableTags = None

    def getAvailableImages(self):
        if self.repository == 'dockerhub':
            self.getDockerHubImages()
        elif self.repository == 'lscr.io':
            self.getLinuxServerImages()
        elif self.repository == 'ghcr.io':
            self.getGithubImages()
        else:
            raise NotImplementedError(f"Unknown repository {self.repository}")

        self.getValidVersions()
        self.latestAvailableVersion = self.getLatestVersion()

    def getDockerHubImages(self):
        with requests.get(f"https://hub.docker.com/v2/repositories/{self.organisation}/{self.name}/tags?status=active&page_size=100") as r:
            if r.ok:
                results = json.loads(r.text)["results"]
                tags = [result["name"] for result in results]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.name}. Reason: {r.reason}")
        self.availableTags = tags

    def getLinuxServerImages(self):
        with requests.get("https://fleet.linuxserver.io/api/v1/images") as r:
            if r.ok:
                results = json.loads(r.text)["data"]["repositories"]["linuxserver"]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.name}. Reason: {r.reason}")
        for result in results:
            if result["name"] == self.name:
                self.availableTags = [result["version"]]
                break
        if self.availableTags is None:
            raise ValueError(f"Could not find image {self.url} in LinuxServer.io")

    def getGithubImages(self):
        with requests.get(
                url=f"https://api.github.com/orgs/{self.organisation}/packages/container/{self.name}/versions", 
                headers={"Accept": "application/vnd.github+json", "Authorization": f"token {self.conf.githubToken}"},
            ) as r:
            if r.ok:
                results = r.json()
                for result in results:
                    tag = result["metadata"]["container"]["tags"]
                    if len(tag):
                        if self.availableTags is None:
                            self.availableTags = [tag[0]]
                        else:
                            self.availableTags += [tag[0]]
            else:
                log.warning(f"Could not download tags for {self.organisation}/{self.name}. Reason: {r.reason}")

    def extractVersionNumber(self, versionNumber, alldigits=True):
        try:
            version = Version(versionNumber)
            return version
        except InvalidVersion:
            return None

    def getValidVersions(self):
        if self.availableTags is None:
            log.warning(f"No available tags for {self.organisation}/{self.name}.")
        else:
            processedVersions = [self.extractVersionNumber(imageVersion) for imageVersion in self.availableTags]
            self.availableVersions = [Version(key) for key, val in zip(self.availableTags, processedVersions) if val is not None]

    def getLatestVersion(self, branch='release'):
        images = self.availableVersions
        if branch == 'release':
            images = [image for image in images if not image.is_devrelease and not image.is_postrelease and not image.is_prerelease]
        else:
            raise NotImplementedError
        images.sort(reverse=True)
        return images[0]

    def updateCheck(self):
        if self.latestAvailableVersion is None:
            self.getAvailableImages()

        if self.latestAvailableVersion > self.version:
            self.setUpToDate(False)
        else:
            self.setUpToDate(True)

    def setUpToDate(self, upToDate):
        self.upToDate = upToDate
        
        if self.conf.mqtt:
            payload = {
                "state": "OFF" if upToDate else "ON",
                "version": str(self.version),
            }
            if not upToDate:
                payload["available_version"] = str(self.latestAvailableVersion)

            self.mqttClient.publish(f"{self.mqttServiceTopic}", payload=json.dumps(payload))