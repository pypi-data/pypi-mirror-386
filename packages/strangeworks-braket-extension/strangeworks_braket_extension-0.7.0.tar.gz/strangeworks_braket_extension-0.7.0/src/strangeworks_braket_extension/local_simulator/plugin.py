"""plugin.py."""

import logging

from strangeworks_core.types import Resource, SDKCredentials
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin

from .local import instrument_local_simulator

_PLUGIN_NAME = "amazon-braket"
_DISPLAY_NAME = "amazon-braket"
logger = logging.getLogger(__name__)


class LocalSimulatorPlugin(ExtensionsPlugin):
    """Instrument Braket Local Simulators

    Parameters
    ----------
    ExtensionsPlugin : _type_
        extends ExtensionsPlugin
    """

    def __init__(
        self,
        *,
        resource: Resource,
        credentials: SDKCredentials,
        **kwargs,
    ):
        super().__init__(
            name=_PLUGIN_NAME,
            display_name=_DISPLAY_NAME,
            **kwargs,
        )
        self._local_sim_plugin = instrument_local_simulator(
            resource=resource,
            credentials=credentials,
        )

    @classmethod
    def create(
        cls, *, resource: Resource, session_info: SDKCredentials, **kwargs
    ) -> "LocalSimulatorPlugin":
        if "name" in kwargs:
            kwargs.pop("name")

        return cls(
            resource=resource,
            session_info=session_info,
            **kwargs,
        )

    def enable(self):
        self._local_sim_plugin.enable()
        logger.info(f"{self._name} enabled")

    def disable(self):
        logger.warning(f"{self._name} disable not implemented.")
