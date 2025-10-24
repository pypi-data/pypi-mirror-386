"""sw_proxy.py."""

from strangeworks_core.types import Resource, SDKCredentials
from strangeworks_extensions.plugins.instance import InstanceInstrumentation
from strangeworks_extensions.plugins.types import RuntimeWrapper
from strangeworks_extensions.utils import add_logger


def session_wrapper(resource: Resource, credentials: SDKCredentials) -> RuntimeWrapper:
    """Sample Wrapper for create_quantum_task

    Example of how to obtain the AwsSession object (session_obj=fn.__self__) and
    instrument the method of member instance inside that (session_obj.braket_client)

    Instrumenting only the instance/object is a nice plus. However AWS/BOTO is insanely
    overcomplicated and using this approach is a departure from the original motivation
    and philosophy of extensions.

    Parameters
    ----------
    resource : Resource
        _description_
    credentials : SDKCredentials
        _description_

    Returns
    -------
    HandlerFunction
        _description_
    """

    def _wrapper(fn, *args, **kwargs):
        session_obj = fn.__self__
        plugin = InstanceInstrumentation(
            name="create_quantum_task",
            method_name="create_quantum_task",
            handler_func=add_logger,
            instance=session_obj.braket_client,
        )
        plugin.enable()
        # instrument create_quantum_task in braket object.

        return add_logger(fn, *args, **kwargs)

    return _wrapper
