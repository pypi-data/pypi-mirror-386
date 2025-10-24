"""reqs.py."""

import logging
from typing import Protocol

from requests import Response, sessions
from strangeworks_core.types import SDKCredentials

from strangeworks_extensions.plugins.types import ProxySelector
from strangeworks_extensions.sdk import get_sdk_session
from strangeworks_extensions.utils import request_id

logger = logging.getLogger(__name__)


class RequestAPIHandler(Protocol):
    def __call__(self, fn, method: str, url: str, *args, **kwargs) -> Response: ...


def get_proxy_redirect_wrapper(
    *,
    selector: ProxySelector,
    credentials: SDKCredentials,
) -> RequestAPIHandler:
    """Wrapper for the requests.api.request function.

    Intended for scenarios where requests to external providers (IBM, DWave, etc.)
    need to go through a Strangeworks Proxy. The most common scenario is where the
    user wants to use Strangeworks credentials to access/use a resource. The wrapper
    will only direct traffic if the url_selector returns true for the URL that is
    sent to the request call. All other calls will pass through to their original
    destination.

    Care should be taken when selecting which request method to instrument, as using
    this wrapper can affect all traffic from requests. Recommended instrumentation
    targets in order of safety:
    1. Provider uses a custom class which extends requests.session.Session class. Then
    instrument the request method of the custom class (safest)
    2. The request function in the `requests.api` module
    3. The request method in the base Session class in `requests.sessions`. Use this
    option with great caution it will affect majority if not all clients calls.

    Parameters
    ----------
    selector : ProxySelector
        Determines whether a URL should be proxied through Strangeworks. Provides
        Strangeworks Proxy URL for the service.
    credentials : SDKCredentials
        Strangeworks SDK credentials for authentication.

    Returns
    -------
    RequestAPIHandler
        A wrapper function that intercepts and potentially proxies HTTP requests.
    """

    def _wrapper(fn, method: str, url: str, *args, **kwargs):
        if selector.use_proxy(url):
            logger.debug(
                f"use strangeworks proxy: {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
            )
            req = {
                "id": request_id(),
                "provider_request": {
                    "method": method,
                    "url": url,
                    "kwargs": kwargs,
                },
            }
            with get_sdk_session(
                credentials=credentials,
            ) as session:
                return session.request(
                    method="POST",
                    url=selector.proxy_url,
                    json=req,
                )

        logger.debug(
            f"passthrough {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
        )
        with sessions.Session() as session:
            return session.request(method=method, url=url, *args, **kwargs)

    return _wrapper


# def get_session_wrapper(
#     proxy_url: str,
#     credentials: SDKCredentials,
#     ignores: list[str] = [],
# ):
#     """Generate Wrapper for Custom Session Implementations.

#     Calls to paths in the ignores list bypass the proxy service. All other calls
#     are sent to the proxy where the call will be sent to its final destination with
#     the Strangeworks api key, etc for that application. Calls which generate
#     job artifacts should not have their path in the ignores list.

#     Parameters
#     ----------
#     proxy_url: str
#         URL for the provider proxy service
#     ignores: list[str]
#         List of provider paths to ignore. These will go through untouched.
#     """

#     def __wrapper(fn, method: str, url: str, *args, **kwargs):
#         """Wrap Requests Session Class.

#         The function fn should almost always be `request` The proxy service should
#         have the logic for redirecting requests, etc.

#         See https://github.com/psf/requests/blob/v2.32.3/src/requests/sessions.py#L500
#         """
#         if url in ignores:
#             logger.debug(
#                 f"passthrough {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
#             )
#             return fn(method=method, url=url, *args, **kwargs)

#         # path is not in ignores list. use sw proxy.
#         logger.debug(
#             f"use strangeworks proxy: {fn.__name__}, method: {method}, url: {url} args: {args}, kwargs: {kwargs}"  # noqa
#         )

#         req = {
#             "id": request_id(),
#             "provider_request": {
#                 "method": method,
#                 "url": url,
#                 "kwargs": kwargs,
#             },
#         }

#         with get_sdk_session(
#             credentials=credentials,
#         ) as session:
#             return session.request(
#                 method="POST",
#                 url=proxy_url,
#                 json=req,
#                 headers={
#                     "Content-Type": "application/json",
#                 },
#             )

#     return __wrapper
