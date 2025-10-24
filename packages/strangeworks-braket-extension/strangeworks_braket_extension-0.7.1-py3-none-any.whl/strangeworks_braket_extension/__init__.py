"""__init__.py."""

import logging

from strangeworks_core.types import Resource, SDKCredentials
from strangeworks_extensions.plugins.plugin import ExtensionsPlugin

from .aws.serverless import instrument_serverless
from .local_simulator.local import instrument_local_simulator

_local_sim_plugin = None

logger = logging.getLogger(__name__)


class AWSExtension(ExtensionsPlugin):
    def __init__(self, resource: Resource, credentials: SDKCredentials):
        self._local_sim = instrument_local_simulator(
            resource=resource, credentials=credentials
        )
        self._aws_session_plugin = instrument_serverless(
            resource=resource, credentials=credentials
        )

    @classmethod
    def create(cls, resource: Resource, credentials: SDKCredentials) -> "AWSExtension":
        return cls(
            resource=resource,
            credentials=credentials,
        )

    def enable(self, *args, **kwargs):
        logger.debug("start enabling AWSExtension plugin")
        try:
            self._aws_session_plugin.enable()
        except Exception as ex:
            logger.exception(ex)
        try:
            self._local_sim.enable()
        except Exception as ex:
            logger.exception(ex)
        logger.debug("completed enabling AWSExtension plugin")

    def disable(self, *args, **kwargs):
        logger.debug(f"start disabling {self.__class__.name}")
        try:
            self._aws_session_plugin.disable()
        except Exception as ex:
            logger.exception(ex)
        try:
            self._local_sim.disable()
        except Exception as ex:
            logger.exception(ex)
        logger.debug(f"finished disabling {self.__class__.name}")


def setup(resource: Resource, credentials: SDKCredentials) -> AWSExtension:
    """Setup Amazon Braket Extension

    Parameters
    ----------
    resource : Resource
        _description_
    credentials : SDKCredentials
        _description_
    """
    global _local_sim_plugin
    _local_sim_plugin = instrument_local_simulator(
        resource=resource, credentials=credentials
    )
    return AWSExtension(resource=resource, credentials=credentials)
