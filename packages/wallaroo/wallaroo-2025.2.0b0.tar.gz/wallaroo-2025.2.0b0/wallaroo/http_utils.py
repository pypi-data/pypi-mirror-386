from typing import TYPE_CHECKING, Optional

import httpx

from .version import _user_agent

if TYPE_CHECKING:
    from .client import Client


if TYPE_CHECKING:
    # Imports that happen below in methods to fix circular import dependency
    # issues need to also be specified here to satisfy mypy type checking.
    pass


def _get_base_headers():
    return {
        "user-agent": _user_agent,
    }


def _setup_http_client(
    client: "Client", headers: Optional[dict] = None
) -> "httpx.Client":
    base_headers = _get_base_headers()
    if headers:
        base_headers.update(headers)
    client._http_client = httpx.Client(
        base_url=client.api_endpoint,
        auth=client.auth,
        headers=base_headers,
        timeout=httpx.Timeout(client.timeout),
        limits=httpx.Limits(keepalive_expiry=client.timeout),
    )
    return client._http_client
