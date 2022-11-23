import json
import logging
from packaging.version import Version, InvalidVersion

log = logging.getLogger('main')

class DockerService:
    def __init__(self, file, service, image, conf, mqtt_client=None, version=None) -> None:
        url = image.split(':')[0]

        if version is None:
            version = image.split(':')[1] if ':' in image else None

        package = url.split('/')[-1]
        organisation = url.split('/')[-2] if len(url.split('/')) > 1 else 'library'
        repository = url.split('/')[0] if len(url.split('/')) == 3 else 'dockerhub'
        repository = repository.replace('.', '_')
        
        log.info(f'Loading repository {repository}')
        repo = __import__(f"repos.{repository}", fromlist=['something'])
        self.repo = repo.Repository(organisation, package, conf)
    
        self.name = service
        self.file = file
        self.package = package
        self.url = url
        self.organisation = organisation
        self.repository = repository
        self.conf = conf
        self.mqtt_client = mqtt_client
        self.mqtt_service_topic = f"{self.conf.mqtt.topic}/{self.file}/{self.name}/info"

        try:
            self.version = Version(version)
        except (InvalidVersion, TypeError):
            self.version = Version("0.0.0")

        self.latest_available_version = None

    
    def get_latestversion(self, branch='release'):
        images = self.repo.get_images()

        if branch == 'release':
            images = [image for image in images if not image.is_devrelease and not image.is_postrelease and not image.is_prerelease]
        else:
            raise NotImplementedError
        images.sort(reverse=True)
        self.latest_available_version = images[0]


    def get_availableimages(self):
        available_tags = self.repo.get_images()

        if available_tags is None:
            log.warning(f"No available tags for {self.organisation}/{self.package}.")
        else:
            processed_versions = [self.extract_versionnumber(image_version) for image_version in available_tags]
            self.available_images = [Version(key) for key, val in zip(available_tags, processed_versions) if val is not None]


    def extract_versionnumber(self, version_number, alldigits=True):
        try:
            version = Version(version_number)
            return version
        except InvalidVersion:
            return None


    def update_check(self):
        self.get_latestversion()
        self.set_uptodate()


    def set_version(self, version):
        self.version = version
        
        if self.conf.mqtt.enabled:
            payload = {
                "installed_version": str(self.version),
            }
            self.mqtt_client.publish(self.mqtt_service_topic, payload=json.dump(payload))


    def set_uptodate(self):
        self.uptodate = self.version == self.latest_available_version

        if self.conf.mqtt.enabled:
            payload = {
                "installed_version": str(self.version),
                "latest_version": str(self.latest_available_version),
            }

            self.mqtt_client.publish(self.mqtt_service_topic, payload=json.dumps(payload))
