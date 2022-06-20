import logging
import sys
from functools import cached_property

from amcrest import AmcrestCamera
from slugify import slugify


logger = logging.getLogger(__name__)


class CameraClient:
    def __init__(self, host: str, port: str, username: str, password: str) -> None:

        if not host:
            logger.error("Please set the AMCREST_HOST environment variable")
            sys.exit(1)

        if not password:
            logger.error("Please set the AMCREST_PASSWORD environment variable")
            sys.exit(1)

        # Connect to camera
        self.client = AmcrestCamera(host, port, username, password).camera

        # Fetch camera details
        logger.info("Fetching camera details...")
        logger.info(f"Device type: {self.device_type}")
        logger.info(f"Serial number: {self.serial_number}")
        logger.info(f"Software version: {self.amcrest_version}")
        logger.info(f"Device name: {self.name}")

    @cached_property
    def serial_number(self) -> str:
        """Get serial number from Amcrest camera"""
        return self.client.serial_number

    @cached_property
    def version(self) -> str:
        return self.client.software_information[0].replace("version=", "").strip()

    @cached_property
    def name(self) -> str:
        return self.client.machine_name.replace("name=", "").strip()

    @cached_property
    def device_slug(self) -> str:
        return slugify(self.name, separator="_")

    @cached_property
    def build_version(self) -> str:
        return self.client.software_information[1].strip()

    @cached_property
    def amcrest_version(self) -> str:
        return f"{self.version} ({self.build_version})"

    @cached_property
    def device_type(self) -> str:
        return self.client.device_type.replace("type=", "").strip()

    @cached_property
    def is_ad410(self) -> bool:
        return self.device_type == "AD410"

    @cached_property
    def is_ad110(self) -> bool:
        return self.device_type == "AD110"

    @cached_property
    def is_doorbell(self) -> bool:
        return self.is_ad410 or self.is_ad110
