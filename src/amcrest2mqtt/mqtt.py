import json
import logging
import os
import sys
from dataclasses import dataclass
from typing import Any, Dict

from paho.mqtt.client import MQTT_ERR_SUCCESS, Client, error_string  # type: ignore

logger = logging.getLogger(__name__)


@dataclass
class MqttClientTLS:
    ca_certs: str
    certfile: str
    keyfile: str
    cert_reqs: str
    version: str


class MqttClient:
    def __init__(
        self,
        host: str,
        port: str,
        username: str = "",
        password: str = "",
        tls_config: MqttClientTLS = None,
    ) -> None:

        # Connect to MQTT
        self.client = Client(
            client_id=f"amcrest2mqtt_{str(os.urandom(8))}", clean_session=True
        )
        self.client.on_disconnect = self.on_mqtt_disconnect
        # self.client.will_set(
        #    topics["status"], payload="offline", qos=self.mqtt_qos, retain=True
        # )

        if tls_config:
            self.client.tls_set(
                ca_certs=tls_config.ca_certs,
                certfile=tls_config.certfile,
                keyfile=tls_config.keyfile,
                cert_reqs=tls_config.cert_reqs,
                tls_version=tls_config.version,
            )
        else:
            self.client.username_pw_set(username, password=password)

        try:
            self.client.connect(host, port=port)
            self.client.loop_start()
        except ConnectionError as error:
            logger.error(f"Could not connect to MQTT server: {error}")
            sys.exit(1)

    def publish(self, topic, payload, qos=0, exit_on_error=True, as_json=False):
        """Publish message to MQTT topic"""
        payload = json.dumps(payload) if as_json else payload
        msg = self.client.publish(
            topic,
            payload=payload,
            qos=qos,
            retain=True,
        )

        if msg.rc == MQTT_ERR_SUCCESS:
            msg.wait_for_publish(2)
            return

        logger.error(f"Error publishing MQTT message: {error_string(msg.rc)}")

        if exit_on_error:
            self.exit_gracefully(msg.rc, skip_mqtt=True)

    def on_mqtt_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.error("Unexpected MQTT disconnection")
            self.client.disconnect()

    def exit_gracefully(
        self, topic: Dict[str, Any], rc: int, skip_mqtt: bool = False
    ) -> None:
        logger.info("MqttClient exiting")
        if self.client.is_connected() and not skip_mqtt:
            self.publish(topic, "offline", exit_on_error=False)
            self.client.disconnect()

        # Use os._exit instead of sys.exit to ensure an MQTT disconnect event causes the program to exit correctly as they
        # occur on a separate thread
        os._exit(rc)
