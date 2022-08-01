import logging

log = logging.getLogger('main')

# empty class
class EmptyClass:
    def __init__(self, conf):
        for attr in dir(conf):
            if not attr.startswith('__'):
                setattr(self, attr, getattr(conf, attr))

# MQTT utilities
def on_connect(client, userdata, flags, rc):
    log.info("MQTT connected with result code "+str(rc))


def on_message(client, userdata, msg):
    log.info(msg.topic+" "+str(msg.payload))