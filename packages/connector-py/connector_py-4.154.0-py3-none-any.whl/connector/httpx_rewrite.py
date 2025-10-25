import contextvars
import logging
from collections.abc import Generator
from contextlib import contextmanager

import httpx
from connector_sdk_types.generated import ErrorCode
from gql.transport.httpx import HTTPXAsyncTransport as GqlHTTPXAsyncTransport
from urllib3.util.url import Url, parse_url

from connector.oai.errors import ConnectorError
from connector.response_logging import (
    CONTENT_MAX_LENGTH,
    ResponseLogRecord,
    create_response_logger,
    redact_sensitive_data,
)

logger = logging.getLogger("integration-connectors.sdk")
GLOBAL_REQUEST_TIMEOUT = httpx.Timeout(300.0)  # 5 minutes


# Create response logger (same as original)
response_logger = create_response_logger("integration-connectors.sdk.api_response")

LUMOS_PROXY_URL: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "LUMOS_PROXY_URL", default=None
)
LUMOS_PROXY_HEADERS: contextvars.ContextVar[httpx.Headers] = contextvars.ContextVar(
    "LUMOS_PROXY_HEADERS", default=httpx.Headers()
)


@contextmanager
def proxy_settings(
    *, proxy_url: str | None, proxy_headers: dict[str, str] | httpx.Headers | None = None
) -> Generator[None, None, None]:
    """
    Set context to run some httpx requests that are rewritten to a proxy.

    Example:

      from httpx_rewrite import AsyncClient, proxy_settings

      with proxy_settings(proxy_url="https://mitm.lumos.com/whatever/path", proxy_headers={"password":"swordfish"}):
          client = AsyncClient()
          await client.get("https://a-real-url-to-call/different/path")
    """
    LUMOS_PROXY_URL.set(proxy_url)
    LUMOS_PROXY_HEADERS.set(httpx.Headers(proxy_headers))
    yield


def get_proxy_url() -> str | None:
    """Return the current URL requests should proxy to. Set this with proxy_settings()"""
    return LUMOS_PROXY_URL.get()


def get_proxy_headers() -> httpx.Headers:
    """Return the current headers that should be attached to proxied requests. Set this with proxy_settings()"""
    return LUMOS_PROXY_HEADERS.get()


def log_response(response: httpx.Response):
    """Log HTTP response (restored original httpx_rewrite logic)"""
    content = response.text

    if len(content) > CONTENT_MAX_LENGTH:
        content = content[: CONTENT_MAX_LENGTH // 2] + " ... " + content[-CONTENT_MAX_LENGTH // 2 :]

    content = redact_sensitive_data(content)
    url = redact_sensitive_data(str(response.url))
    headers = redact_sensitive_data(dict(response.headers))

    content_hash = ""
    try:
        content_hash = str(hash(content))
    except Exception:
        content_hash = "hashing failed"

    record = ResponseLogRecord(
        name=response_logger.name,
        level=response_logger.level,
        pathname="",
        lineno=0,
        msg=f"Got an external response: [{response.request.method}][{response.status_code}] {url}",
        args=(),
        exc_info=None,
    )

    record.method = str(response.request.method)
    record.url = url
    record.status_code = response.status_code
    record.headers = headers
    record.content = content
    record.content_hash = content_hash

    response_logger.handle(record)


class AsyncClient(httpx.AsyncClient):
    """
    A slightly modified version of httpx.AsyncClient, that may rewrite requests to go to a proxy.

    Requests will be rewritten when run within the proxy_settings() context.

    Rewritten requests...
    1. will go to the proxy URL
    2. will have the original request line (including fragment) preserved in the header `X-Forward-To`
    3. will have their headers preserved, EXCEPT FOR...
       a. `Host` will be set to the proxy host
       b. Additional headers will be set, and overwrite any passed-in headers, from
         - the LUMOS_PROXY_HEADERS environment variable (as JSON)
         - the accumulated calls to this module's `add_proxy_headers` function
    """

    def will_rewrite_request(self) -> bool:
        return bool(get_proxy_url())

    def __init__(self, *args, **kwargs):
        if "timeout" not in kwargs:
            kwargs["timeout"] = GLOBAL_REQUEST_TIMEOUT
        super().__init__(*args, **kwargs)

    async def send(self, request: httpx.Request, **kwargs) -> httpx.Response:
        proxy_host = get_proxy_url()
        if proxy_host:
            logger.warning("Proxying all requests to %s", proxy_host)
            override = parse_url(proxy_host)
        else:
            response = await super().send(request, **kwargs)
            log_response(response)
            return response

        # Update request URL
        url = str(request.url)
        updated = Url(
            scheme=override.scheme,
            host=override.host,
            port=override.port,
            path=override.path,
            query=override.query,
        )

        # Rewrite headers
        new_headers = request.headers.copy()
        new_headers["X-Forward-To"] = url
        new_headers["Host"] = Url(host=override.host, port=override.port).url
        proxy_headers = get_proxy_headers()
        for header, value in proxy_headers.items():
            new_headers[header] = value

        # Get request body if applicable
        if request.method in ("POST", "PUT", "PATCH"):
            content = request.content or bytes([])
        else:
            content = None

        new_request = httpx.Request(
            method=request.method,
            url=updated.url,
            headers=new_headers,
            content=content,
        )

        # Log everything when using the proxy for debugging
        logger.debug("Sending request to proxy: %s", new_request.url)
        logger.debug("Request method: %s", new_request.method)
        response = await super().send(new_request, **kwargs)
        logger.debug("Request headers: %s", [(k, v) for k, v in response.request.headers.items()])
        logger.debug("Request body: %s", response.request.content)
        logger.debug("Response headers: %s", [(k, v) for k, v in response.headers.items()])
        truncated_response = response.text[:1000] + "..." if len(response.text) > 1000 else ""
        logger.debug("Response: %s", truncated_response)
        logger.debug("Response status code: %s", response.status_code)

        # Create a debug hint if the proxy/service is not working as expected
        proxy_status = int(response.headers.get("x-lumos-sip-status-code") or response.status_code)
        target_status = response.headers.get("x-lumos-target-hostname-status-code")
        if proxy_status != 200:
            hint = (
                "There is something wrong with the proxy itself or you are giving it a bad "
                f"arn value. Proxy returned code {proxy_status}; "
                "sort this out first before troubleshooting the target service."
            )
            hint_status = proxy_status
            hint_url = new_request.url

        elif target_status is not None and not str(target_status).startswith("2"):
            hint = (
                f"The target service returned code {target_status}, "
                "the proxy is working as expected."
            )
            hint_status = target_status
            hint_url = request.url

        if "hint" in locals():
            raise ConnectorError(
                error_code=ErrorCode.INVALID_RESPONSE,
                message=f"[{hint_status}][{hint_url}] {hint} Original response: {response.text}",
                app_error_code="proxy_mode_error_debug_hint",
            )

        return response


class HTTPXAsyncTransport(GqlHTTPXAsyncTransport):
    async def connect(self):
        # Call the superclass...
        await super().connect()

        # ... and then override its result
        self.client = AsyncClient(**self.kwargs)
