"""local.py."""

import logging
from typing import Any, Tuple

from braket.devices.local_simulator import LocalSimulator
from braket.tasks import (
    AnnealingQuantumTaskResult,
    GateModelQuantumTaskResult,
    PhotonicModelQuantumTaskResult,
)
from braket.tasks.local_quantum_task import LocalQuantumTask
from strangeworks_braket_extension.utils import _serialize_result
from strangeworks_core.platform.session import StrangeworksSession
from strangeworks_core.types import JobStatus, Resource, SDKCredentials
from strangeworks_extensions.plugins.instrumentation import (
    ClassMethodSpec,
    Instrumentation,
)
from strangeworks_extensions.sdk import get_sdk_session as get_session
from strangeworks_extensions.types import ExtensionsRequest, InputArgs, SWJobInfo

logger = logging.getLogger(__name__)

_SW_EXTENSIONS_ROUTER_PATH = "/products/sdk-extensions/jobs/create"
__AMAZON_BRAKET_LOCAL_DEVICE_MODULE_NAME = "braket.devices.local_simulator"
__AMAZON_BRAKET_LOCAL_DEVICE_CLASS_NAME = "LocalSimulator"


_spec = ClassMethodSpec(
    module_name=__AMAZON_BRAKET_LOCAL_DEVICE_MODULE_NAME,
    class_name=__AMAZON_BRAKET_LOCAL_DEVICE_CLASS_NAME,
    method_name="run",
)


def process_result(
    *,
    local_task: LocalQuantumTask,
    resource: Resource,
    simulator: LocalSimulator | None = None,
    args: Tuple[Any, ...] | None = None,
    kwargs: dict[str, Any] = {},
) -> ExtensionsRequest:
    """Generate an Extensions Router Request from Local Simulator Result.

    The simulator is used to convert the Circuit object into its intermediate
    representation (IR) so that it can be sent over HTTP. The simulator should
    not be used for anything else.

    The resource object is used by the platform to determine which workspace to
    associate the result with.
    Parameters
    ----------
    local_task : LocalQuantumTask
        Result from local simulator
    resource : Resource
        Strangeworks resource.
    simulator : LocalSimulator | None, optional
        Simulator used to generate result, by default None
    args : Tuple | None, optional
        Arguments sent to simulator run method, by default None
    kwargs : dict[str, Any] | None, optional
        Keyword arguments sent to simulator run method, by default None

    Returns
    -------
    ExtensionsRequest
        _description_
    """
    task_spec = None
    shots: int | None = None
    inputs: dict | None = None
    _kwargs_copy = {**kwargs} if kwargs else {}
    _tags: list[str] = ["local_simulator", "braket"]
    if simulator:
        _tags.append(simulator.name)
        task_specification = (
            args[0] if args and len(args) >= 1 else kwargs.get("task_specification")
        )
        shots = args[1] if args and len(args) >= 2 else kwargs.get("shots")
        inputs = args[2] if args and len(args) >= 3 else kwargs.get("inputs")
        if task_specification:
            task_spec = simulator._construct_payload(task_specification, inputs, shots)

        _kwargs_copy["task_specification"] = task_spec.json()
        if args and len(args) >= 2:
            _kwargs_copy["shots"] = shots
        if args and len(args) >= 3:
            _kwargs_copy["inputs"] = inputs

    # res: GateModelQuantumTaskResult = local_task.result()
    res: (
        GateModelQuantumTaskResult
        | AnnealingQuantumTaskResult
        | PhotonicModelQuantumTaskResult
    ) = local_task.result()
    _serialized_result = _serialize_result(res)
    return ExtensionsRequest(
        product_slug=resource.product.slug,
        resource_slug=resource.slug,
        input_args=InputArgs(
            kwargs=_kwargs_copy,
        ),
        result=_serialized_result,
        sw_job_settings=SWJobInfo(
            status=JobStatus.COMPLETED,
            tags=_tags,
        ),
    )


def local_handler(resource: Resource, credentials: SDKCredentials):
    """Generate a Handler for Functions that Run Locally

    For functions that generate results and other artifacts
    by running local processes like simulators, etc.

    Parameters
    ----------
    resource: Resource
        User resource used to identify which workspace to associate results and
        artifacts with.
    session: SDKSessionInfo
        Settings used to connect to the Strangeworks platform.

    Returns
    -------
        :Any
        The return value from the original function.
    """

    def _wrapper(fn, *args, **kwargs):
        """Wrapper for Generating Strangeworks Platform Artifacts (Jobs, etc)

        These wrappers are used to grab job artifacts generated from certain functions.

        Parameters
        ----------
        fn : function
            function whose inputs/outputs will contain artifacts.

        Returns
        -------
        : Any
            original return value of function
        """
        logger.info(f"[PATCHED] {fn.__name__} args={args}, kwargs={kwargs}")

        local_task: LocalQuantumTask = fn(*args, **kwargs)

        # if we get this far and actually have a result, return result regardless of
        # whether the result was uploaded.
        try:
            obj_maybe: LocalSimulator = fn.__self__
            req: ExtensionsRequest = process_result(
                local_task=local_task,
                resource=resource,
                simulator=obj_maybe,
                args=args,
                kwargs=kwargs,
            )
            logger.debug(f"extension request: {req}")

            sw_session: StrangeworksSession = get_session(
                credentials=SDKCredentials(
                    host_url=credentials.host_url, api_key=credentials.api_key
                ),
            )
            _url: str = f"{credentials.host_url}{_SW_EXTENSIONS_ROUTER_PATH}"

            _res = sw_session.request(
                method="POST",
                url=_url,
                json=req.model_dump(exclude_none=True),
                headers={
                    "Content-Type": "application/json",
                },
            )
            _res.raise_for_status()

        except Exception as ex:
            logger.exception(ex)
        finally:
            return local_task

    return _wrapper


def instrument_local_simulator(resource: Resource, credentials: SDKCredentials):
    fn = local_handler(resource=resource, credentials=credentials)
    return Instrumentation(
        name="aws_braket_sim_plugin",
        spec=_spec,
        handler_func=fn,
    )
