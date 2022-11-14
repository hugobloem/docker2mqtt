<div align=center>
<h1>docker2mqtt</h1>
Update your Docker containers from Home Assistant with MQTT.
</div>

## Getting started
At the moment I have Docker set up as a Swarm and I deploy containers using stack files. These stack files are read, changed and deployed by docker2mqtt. At the moment three repositories are supported: Docker Hub, GitHub packages, and Linuxserver.io. What follows is a short guide to set this up in your environment.

1. Clone this project using the green button in the top right corner.
2. Build the image using the following docker command: `docker build -t docker2mqtt .`
3. Adapt the following command such that your stacks folder and configuration file is included and run it. `docker run -d -v <YOUR STACKS FOLDER>:/stacks -v <YOUR CONFIGURATION FILE>:/configuration.yaml -v /var/run/docker.sock:/var/run/docker.sock --name docker2mqtt docker2mqtt`
4. The containers specified in your stacks files should now automatically be discovered by Home Assistant. If an update is available the update entity will let you install it by simply clicking `install`.

## Configuration
The table below contains the different configuration options available in the yaml file.

| Master key | Key | Default | Description |
|------------|-----|--------|-------------|
|`general`   |`input_dir` | `/stacks/` | Location of the stacks folder (no need to change this if the stacks folder is mounted in the correct location. |
|  | `log_level` | `INFO` | Amount of logging that is being produced. Choose from DEBUG, INFO, WARNING, ERROR, CRITICAL. |
|| `github_token` | `null `| If packages are being downloaded from the GitHub repository a GitHub token is needed to access the API. |
||`sleep_time`| 3600 | Interval in seconds to check for new updates. |
|`mqtt`| `enabled` | `true` | Whether to use MQTT or not (mostly for testing purposes). |
|| `host` | `null` | Hostname of the MQTT broker. |
|| `port` | 1883 | Port of the MQTT broker. |
|| `topic` | `docker2mqtt` | MQTT topic to publish docker2mqtt messages on |
|`homeassistant`| `enabled` | `true` | Whether to let Home Assistant auto-discover docker2mqtt entities. |
|| `discovery_topic` | `homeassistant` | MQTT topic used for Home Assistant auto-discovery. |
|| `grouping_device` | `null` | If you want all update entities to appear under a single device in Home Assistant specify this parameter. Otherwise, all update entities will be discovered as a different device. |

## Limitations
As this is project is still a work-in-progress there are a few limitations: 
- I have only tested Docker Swarm setups. Docker compose files may work but this is not tested.
- The MQTT update entity currently does not support progress. Hence, if you press install in Home Assistant there will be no feedback as to whether the update is actually installed.
- This container MUST be installed on a swarm manager node. This is a limitation from Docker that only updates to a stack can be made from a manager node.

Furthermore, the documentation is not 100% up to date. I do plan to go through all the codes and write explanations where needed.

## Future updates
Here is a list of features that I would like to add to this project in due course in no particular order and without a timeframe. 
- [ ] Git support: once a container is updated commit the change in the stacks folder. 
- [ ] Update progress: publish the progress of an update to Home Assistant.
- [ ] Web interface: add a web interface similar to what is provided by zigbee2mqtt. 

## Notes
If you have any issues or questions please let me know by opening an issue here on Github. If you like this project please consider starring it. Lastly, if you would like to contribute, please open a pull request to submit your suggestion.
