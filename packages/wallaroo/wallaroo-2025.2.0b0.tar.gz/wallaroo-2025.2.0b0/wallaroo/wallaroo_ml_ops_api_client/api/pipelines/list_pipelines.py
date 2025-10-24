from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_pipelines_body import ListPipelinesBody
from ...models.list_pipelines_response_200 import ListPipelinesResponse200
from ...types import Response


def _get_kwargs(
    *,
    body: ListPipelinesBody,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/v1/api/pipelines/list_pipelines",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[ListPipelinesResponse200]:
    if response.status_code == 200:
        response_200 = ListPipelinesResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[ListPipelinesResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListPipelinesBody,
) -> Response[ListPipelinesResponse200]:
    """Lists the publishes for a Pipeline. This aggregates publishes for all versions of that Pipeline.

    Args:
        body (ListPipelinesBody): Request to list published pipelines.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListPipelinesResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListPipelinesBody,
) -> Optional[ListPipelinesResponse200]:
    """Lists the publishes for a Pipeline. This aggregates publishes for all versions of that Pipeline.

    Args:
        body (ListPipelinesBody): Request to list published pipelines.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListPipelinesResponse200
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListPipelinesBody,
) -> Response[ListPipelinesResponse200]:
    """Lists the publishes for a Pipeline. This aggregates publishes for all versions of that Pipeline.

    Args:
        body (ListPipelinesBody): Request to list published pipelines.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ListPipelinesResponse200]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: ListPipelinesBody,
) -> Optional[ListPipelinesResponse200]:
    """Lists the publishes for a Pipeline. This aggregates publishes for all versions of that Pipeline.

    Args:
        body (ListPipelinesBody): Request to list published pipelines.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ListPipelinesResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
