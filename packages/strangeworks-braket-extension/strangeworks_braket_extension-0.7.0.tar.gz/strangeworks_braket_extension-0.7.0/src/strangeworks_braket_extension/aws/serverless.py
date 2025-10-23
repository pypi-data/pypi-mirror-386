"""session.py."""

import logging
from typing import Any
from urllib.parse import urljoin

from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
)
from strangeworks_core.platform.session import StrangeworksSession
from strangeworks_core.types import JobStatus, Resource, SDKCredentials
from strangeworks_extensions.plugins.types import ClassMethodSpec, RuntimeWrapper
from strangeworks_extensions.sdk import get_sdk_session
from strangeworks_extensions.types import ExtensionsRequest, SWJobInfo

from strangeworks_braket_extension.aws.types import BraketConfig, BraketServerless
from strangeworks_braket_extension.utils import _serialize_result

_BRAKET_AMAZON_SESSION_MODULE_NAME = "braket.aws.aws_quantum_task"
_BRAKET_AMAZON_SESSION_CLASS_NAME = "AwsQuantumTask"
_BRAKET_AMAZON_SESSION_METHOD_NAME = "result"

_SW_EXTENSIONS_ROUTER_PATH = "/products/sdk-extensions/jobs/create"
_PLUGIN_NAME = "AwsSessionPlugin"
_SW_PRODUCT_SLUG = "amazon-braket"
_RESOURCE_CONFIG_KEY = "AMAZON_BRAKET_CONFIG"

logger = logging.getLogger(__name__)


def get_device_name(device_arn: str) -> str | None:
    if device_arn:
        tokens = device_arn.split("/")
        if tokens:
            return tokens[-1]
    return None


def process_result(
    *,
    resource: Resource,
    braket_result: (
        GateModelQuantumTaskResult
        | AnnealingQuantumTaskResult
        | PhotonicModelQuantumTaskResult
    ),
) -> ExtensionsRequest:
    _tags = ["braket"]
    device_name = get_device_name(braket_result.task_metadata.deviceId)
    if device_name:
        _tags.append(device_name)
    return ExtensionsRequest(
        product_slug=_SW_PRODUCT_SLUG,
        resource_slug=resource.slug,
        result=_serialize_result(braket_result),
        sw_job_settings=SWJobInfo(
            external_identifier=braket_result.task_metadata.id,
            status=JobStatus.COMPLETED,
            tags=_tags,
        ),
    )


def _results_handler(
    resource: Resource,
    credentials: SDKCredentials,
) -> RuntimeWrapper:
    """Generate Function to Handle Results and Generate ExtensionsRequest

    Parameters
    ----------
    resource : Resource
        resource to identify which Strangeworks platform user + workspace owns the job.
    credentials : SDKCredentials
        credentials associated with the workspace + user.

    Returns
    -------
    HandlerFunction
        function that takes the device result and returns an ExtensionsRequest
    """

    def _wrapper(fn, *args, **kwargs):
        _result = fn(*args, **kwargs)

        try:
            req: ExtensionsRequest = process_result(
                resource=resource, braket_result=_result
            )
            sw_session: StrangeworksSession = get_sdk_session(
                credentials=credentials,
            )
            _url: str = urljoin(credentials.host_url, _SW_EXTENSIONS_ROUTER_PATH)

            _res = sw_session.request(
                method="POST",
                url=_url,
                json=req.model_dump(exclude_none=True),
                headers={
                    "Content-Type": "application/json",
                },
            )
            _res.raise_for_status()
        finally:
            return _result

    return _wrapper


def instrument_serverless(
    resource: Resource,
    credentials: SDKCredentials,
):
    fn = _results_handler(resource=resource, credentials=credentials)

    sw_cfg: BraketConfig | None = None
    if resource.configurations:
        for cfg in resource.configurations:
            if cfg.key == _RESOURCE_CONFIG_KEY:
                braket_config: dict[str, Any] | None = cfg.valueJson
                if braket_config:
                    sw_cfg = BraketConfig(**braket_config)

    return BraketServerless(
        braket_cfg=sw_cfg,
        name=_PLUGIN_NAME,
        spec=ClassMethodSpec(
            module_name=_BRAKET_AMAZON_SESSION_MODULE_NAME,
            class_name=_BRAKET_AMAZON_SESSION_CLASS_NAME,
            method_name=_BRAKET_AMAZON_SESSION_METHOD_NAME,
        ),
        handler_func=fn,
    )
