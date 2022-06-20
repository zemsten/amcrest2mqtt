import asyncio
import logging
import os
from typing import Any, Dict

from amcrest import AmcrestError

from amcrest2mqtt import __version__
from amcrest2mqtt.camera import CameraClient
from amcrest2mqtt.mqtt import MqttClient
from amcrest2mqtt.util import to_gb


logger = logging.getLogger(__name__)
logger.setLevel(level=logging.DEBUG)


def main() -> None:
    """Main"""

    logger.info(f"App Version: {__version__}")

    amcrest_host = os.getenv("AMCREST_HOST")
    amcrest_port = os.getenv("AMCREST_PORT", "80")
    amcrest_username = os.getenv("AMCREST_USERNAME", "admin")
    amcrest_password = os.getenv("AMCREST_PASSWORD")

    storage_poll_interval = int(os.getenv("STORAGE_POLL_INTERVAL", 3600))

    mqtt_host = os.getenv("MQTT_HOST") or "localhost"
    mqtt_qos = os.getenv("MQTT_QOS", "0")
    mqtt_port = os.getenv("MQTT_PORT", "1883")
    mqtt_username = os.getenv("MQTT_USERNAME")
    mqtt_password = os.getenv("MQTT_PASSWORD")  # can be None
    mqtt_tls_enabled = os.getenv("MQTT_TLS_ENABLED") == "true"
    mqtt_tls_ca_cert = os.getenv("MQTT_TLS_CA_CERT")
    mqtt_tls_cert = os.getenv("MQTT_TLS_CERT")
    mqtt_tls_key = os.getenv("MQTT_TLS_KEY")

    home_assistant = os.getenv("HOME_ASSISTANT") == "true"
    home_assistant_prefix = os.getenv("HOME_ASSISTANT_PREFIX") or "homeassistant"

    camera = CameraClient(
        host=amcrest_host,
        port=amcrest_port,
        username=amcrest_username,
        password=amcrest_password,
    )

    mqtt_client = MqttClient(
        host=mqtt_host,
        port=int(mqtt_port),
        username=mqtt_username,
        password=mqtt_password,
    )

    # MQTT topics
    topics = {
        "config": f"amcrest2mqtt/{camera.serial_number}/config",
        "status": f"amcrest2mqtt/{camera.serial_number}/status",
        "event": f"amcrest2mqtt/{camera.serial_number}/event",
        "motion": f"amcrest2mqtt/{camera.serial_number}/motion",
        "doorbell": f"amcrest2mqtt/{camera.serial_number}/doorbell",
        "human": f"amcrest2mqtt/{camera.serial_number}/human",
        "storage_used": f"amcrest2mqtt/{camera.serial_number}/storage/used",
        "storage_used_percent": f"amcrest2mqtt/{camera.serial_number}/storage/used_percent",
        "storage_total": f"amcrest2mqtt/{camera.serial_number}/storage/total",
        "home_assistant_legacy": {
            "doorbell": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_doorbell/config",
            "human": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_human/config",
            "motion": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_motion/config",
            "storage_used": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_storage_used/config",
            "storage_used_percent": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_storage_used_percent/config",
            "storage_total": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_storage_total/config",
            "version": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_version/config",
            "host": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_host/config",
            "serial_number": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/{camera.device_slug}_serial_number/config",
        },
        "home_assistant": {
            "doorbell": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/doorbell/config",
            "human": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/human/config",
            "motion": f"{home_assistant_prefix}/binary_sensor/amcrest2mqtt-{camera.serial_number}/motion/config",
            "storage_used": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/storage_used/config",
            "storage_used_percent": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/storage_used_percent/config",
            "storage_total": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/storage_total/config",
            "version": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/version/config",
            "host": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/host/config",
            "serial_number": f"{home_assistant_prefix}/sensor/amcrest2mqtt-{camera.serial_number}/serial_number/config",
        },
    }

    # Configure Home Assistant
    if home_assistant:
        logger.info("Writing Home Assistant discovery config...")

        base_config = {
            "availability_topic": topics["status"],
            "qos": mqtt_qos,
            "device": {
                "name": f"Amcrest {camera.device_type}",
                "manufacturer": "Amcrest",
                "model": camera.device_type,
                "identifiers": camera.serial_number,
                "sw_version": camera.amcrest_version,
                "via_device": "amcrest2mqtt",
            },
        }

        if camera.is_doorbell:

            mqtt_client.publish(
                topic=topics["home_assistant_legacy"]["doorbell"], payload=""
            )
            mqtt_client.publish(
                topic=topics["home_assistant"]["doorbell"],
                payload=base_config
                | {
                    "state_topic": topics["doorbell"],
                    "payload_on": "on",
                    "payload_off": "off",
                    "icon": "mdi:doorbell",
                    "name": camera.name,
                    "unique_id": f"{camera.serial_number}.doorbell",
                },
                as_json=True,
            )

        if camera.is_ad410:
            mqtt_client.publish(
                topic=topics["home_assistant_legacy"]["human"], payload=""
            )
            mqtt_client.publish(
                topic=topics["home_assistant"]["human"],
                payload=base_config
                | {
                    "state_topic": topics["human"],
                    "payload_on": "on",
                    "payload_off": "off",
                    "device_class": "motion",
                    "name": f"{camera.name} Human",
                    "unique_id": f"{camera.serial_number}.human",
                },
                as_json=True,
            )

        mqtt_client.publish(topic=topics["home_assistant_legacy"]["motion"], payload="")
        mqtt_client.publish(
            topic=topics["home_assistant"]["motion"],
            payload=base_config
            | {
                "state_topic": topics["motion"],
                "payload_on": "on",
                "payload_off": "off",
                "device_class": "motion",
                "name": f"{camera.name} Motion",
                "unique_id": f"{camera.serial_number}.motion",
            },
            as_json=True,
        )

        mqtt_client.publish(
            topic=topics["home_assistant_legacy"]["version"], payload=""
        )
        mqtt_client.publish(
            topic=topics["home_assistant"]["version"],
            payload=base_config
            | {
                "state_topic": topics["config"],
                "value_template": "{{ value_json.sw_version }}",
                "icon": "mdi:package-up",
                "name": f"{camera.name} Version",
                "unique_id": f"{camera.serial_number}.version",
                "entity_category": "diagnostic",
                "enabled_by_default": False,
            },
            as_json=True,
        )

        mqtt_client.publish(
            topic=topics["home_assistant_legacy"]["serial_number"], payload=""
        )
        mqtt_client.publish(
            topic=topics["home_assistant"]["serial_number"],
            payload=base_config
            | {
                "state_topic": topics["config"],
                "value_template": "{{ value_json.serial_number }}",
                "icon": "mdi:alphabetical-variant",
                "name": f"{camera.name} Serial Number",
                "unique_id": f"{camera.serial_number}.serial_number",
                "entity_category": "diagnostic",
                "enabled_by_default": False,
            },
            as_json=True,
        )

        mqtt_client.publish(topic=topics["home_assistant_legacy"]["host"], payload="")
        mqtt_client.publish(
            topic=topics["home_assistant"]["host"],
            payload=base_config
            | {
                "state_topic": topics["config"],
                "value_template": "{{ value_json.host }}",
                "icon": "mdi:ip-network",
                "name": f"{camera.name} Host",
                "unique_id": f"{camera.serial_number}.host",
                "entity_category": "diagnostic",
                "enabled_by_default": False,
            },
            as_json=True,
        )

        if storage_poll_interval > 0:
            mqtt_client.publish(
                topic=topics["home_assistant_legacy"]["storage_used_percent"],
                payload="",
            )
            mqtt_client.publish(
                topics["home_assistant"]["storage_used_percent"],
                payload=base_config
                | {
                    "state_topic": topics["storage_used_percent"],
                    "unit_of_measurement": "%",
                    "icon": "mdi:micro-sd",
                    "name": f"{camera.name} Storage Used %",
                    "object_id": f"{camera.device_slug}_storage_used_percent",
                    "unique_id": f"{camera.serial_number}.storage_used_percent",
                    "entity_category": "diagnostic",
                },
                as_json=True,
            )

            mqtt_client.publish(
                topic=topics["home_assistant_legacy"]["storage_used"], payload=""
            )
            mqtt_client.publish(
                topic=topics["home_assistant"]["storage_used"],
                payload=base_config
                | {
                    "state_topic": topics["storage_used"],
                    "unit_of_measurement": "GB",
                    "icon": "mdi:micro-sd",
                    "name": f"{camera.name} Storage Used",
                    "unique_id": f"{camera.serial_number}.storage_used",
                    "entity_category": "diagnostic",
                },
                as_json=True,
            )

            mqtt_client.publish(
                topic=topics["home_assistant_legacy"]["storage_total"], payload=""
            )
            mqtt_client.publish(
                topic=topics["home_assistant"]["storage_total"],
                payload=base_config
                | {
                    "state_topic": topics["storage_total"],
                    "unit_of_measurement": "GB",
                    "icon": "mdi:micro-sd",
                    "name": f"{camera.name} Storage Total",
                    "unique_id": f"{camera.serial_number}.storage_total",
                    "entity_category": "diagnostic",
                },
                as_json=True,
            )

    # Main loop
    mqtt_client.publish(topic=topics["status"], payload="online")
    mqtt_client.publish(
        topic=topics["config"],
        payload={
            "version": camera.version,
            "device_type": camera.device_type,
            "device_name": camera.name,
            "sw_version": camera.amcrest_version,
            "serial_number": camera.serial_number,
            "host": amcrest_host,
        },
        as_json=True,
    )

    loop = asyncio.get_event_loop()

    logger.info("Listening for events...")
    try:
        asyncio.ensure_future(refresh_storage_sensors(camera, mqtt_client, topics))
        asyncio.ensure_future(
            poll_device(camera=camera, mqtt_client=mqtt_client, topics=topics)
        )
        loop.run_forever()
    except KeyboardInterrupt:
        loop.close()
        logger.debug("Received KeyboardInterrupt, exitting...")
        mqtt_client.exit_gracefully(topic=topics["status"], rc=0)
        os._exit(1)


async def poll_device(
    camera: CameraClient, mqtt_client: MqttClient, topics: Dict[str, str]
) -> None:
    try:
        async for code, payload in camera.client.async_event_actions("All"):
            if (camera.is_ad110 and code == "ProfileAlarmTransmit") or (
                code == "VideoMotion" and not camera.is_ad110
            ):
                motion_payload = "on" if payload["action"] == "Start" else "off"
                mqtt_client.publish(topic=topics["motion"], payload=motion_payload)
            elif (
                code == "CrossRegionDetection"
                and payload["data"]["ObjectType"] == "Human"
            ):
                human_payload = "on" if payload["action"] == "Start" else "off"
                mqtt_client.publish(topic=topics["human"], payload=human_payload)
            elif code == "_DoTalkAction_":
                doorbell_payload = (
                    "on" if payload["data"]["Action"] == "Invite" else "off"
                )
                mqtt_client.publish(topic=topics["doorbell"], payload=doorbell_payload)

            mqtt_client.publish(topic=topics["event"], payload=payload, as_json=True)
            logger.debug(str(payload))

    except AmcrestError as error:
        logger.error(f"Amcrest error: {error}")
        mqtt_client.exit_gracefully(topic=topics["status"], rc=1)


async def refresh_storage_sensors(
    camera: CameraClient,
    mqtt_client: MqttClient,
    topics: Dict[str, Any],
    polling_interval: int = 3600,
) -> None:
    """Refresh storage sensors from Amcrest camera"""

    while True:
        logger.info("Fetching storage sensors...")
        try:
            storage = camera.client.storage_all

            mqtt_client.publish(
                topic=topics["storage_used_percent"],
                payload=str(storage["used_percent"]),
            )
            mqtt_client.publish(
                topic=topics["storage_used"], payload=to_gb(float(storage["used"][0]))
            )
            mqtt_client.publish(
                topic=topics["storage_total"], payload=to_gb(float(storage["total"][0]))
            )
        except AmcrestError as error:
            logger.warning(f"Error fetching storage information {error}")

    await asyncio.sleep(polling_interval)


if __name__ == "__main__":
    main()
