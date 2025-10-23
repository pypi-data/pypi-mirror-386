import inspect
import logging
from typing import Any, Protocol, Tuple
from urllib.parse import urljoin

from strangeworks_core.platform.session import StrangeworksSession
from strangeworks_core.types import Resource, SDKCredentials
from strangeworks_extensions.sdk import get_sdk_session as get_session
from strangeworks_extensions.types import ExtensionsRequest

_SW_EXTENSIONS_ROUTER_PATH = "/products/sdk-extensions/jobs/create"

logger = logging.getLogger(__name__)

__all__ = ["ResultAdapter", "local_call_handler"]


class ResultAdapter(Protocol):

    def __call__(
        self,
        *,
        result: Any,
        resource: Resource,
        fn_args: Tuple[Any, ...] | None = None,
        fn_kwds: dict[str, Any] | None = None,
        fn_self: object | None = None,
        **kwds,
    ) -> ExtensionsRequest: ...


def local_call_handler(
    resource: Resource,
    session: SDKCredentials,
    process_result: ResultAdapter,
):
    """Handles results from locally made function/method calls and submits them
    to the extensions service.

    Parameters
    ----------
    resource : Resource
        product resource under which this result will be stored.
    session : SDKCredentials
        credentials to use for this workspace.
    process_result : ResultAdapter
        function that processes results and generates an extensions
        service request.
    """

    def _wrapper(fn, *args, **kwargs):
        logger.info(f"[PATCHED] {fn.__name__} args={args}, kwargs={kwargs}")

        res = fn(*args, **kwargs)

        try:
            # collect all the arguments needed for the result generator.
            _args: dict[str, Any] = {
                "result": res,
                "resource": resource,
                "fn_args": args,
                "fn_kwds": kwargs,
            }
            # There are times when the generator function needs the instance
            # object in order to manipulate the result somehow. See AWS local
            # simulator plugin for an example.
            # if fn is a method from a an instance of class but not a class
            # method.
            # Going to keep it simple and ignore unbound methods and class
            # methods for now.
            if inspect.ismethod(fn) and not isinstance(fn.__self__, type):
                _args["fn_self"] = fn.__self__

            logger.debug("processing results to generate extensions request")
            req: ExtensionsRequest = process_result(
                **_args,
            )
            logger.debug(f"generated extensions request: {req}")

            sw_session: StrangeworksSession = get_session(
                credentials=SDKCredentials(
                    host_url=session.host_url, api_key=session.api_key
                ),
            )
            _url: str = urljoin(session.host_url, _SW_EXTENSIONS_ROUTER_PATH)
            logger.debug(f"extensions url: {_url}")

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
            if logger.level == logging.DEBUG:
                logger.exception(ex)
        finally:
            return res

    return _wrapper
