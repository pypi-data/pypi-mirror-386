from abc import ABC
from typing import Mapping

from fastapi.templating import Jinja2Templates
from ..proxies.base import BaseProxy

import logging

logger = logging.getLogger("PluginsLoader")

class Petal(ABC):
    """
    Petal authors only inherit this; NO FastAPI import, no routers.
    """
    name: str
    version: str

    def __init__(self) -> None:
        self._proxies: Mapping[str, BaseProxy] = {}

    # define a startup method that can be overridden
    def startup(self) -> None:
        """
        Called when the petal is started.
        """
        logger.info(f"Starting petal {self.name} ({self.version})")
        pass

    def shutdown(self) -> None:
        """
        Called when the petal is stopped.
        """
        logger.info(f"Shutting down petal {self.name} ({self.version})")
        pass

    async def async_startup(self) -> None:
        """
        Called after startup to handle async operations like MQTT subscriptions.
        """
        logger.info(f"Starting async operations for petal {self.name} ({self.version})")
        pass

    async def async_shutdown(self) -> None:
        """
        Called before shutdown to handle async operations like MQTT unsubscriptions.
        """
        logger.info(f"Shutting down async operations for petal {self.name} ({self.version})")
        pass

    def inject_proxies(self, proxies: Mapping[str, BaseProxy]) -> None:
        # Skip isinstance check for now due to import issues
        # TODO: Debug why isinstance(proxy, BaseProxy) fails during app startup
        self._proxies = proxies

    def inject_templates(self, templates: Mapping[str, Jinja2Templates]) -> None:
        """
        Inject Jinja2 templates into the petal.
        """
        self.templates = templates