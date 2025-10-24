from http import HTTPStatus
from typing import Any, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.post_traces_body import PostTracesBody
from ...models.post_traces_response_201 import PostTracesResponse201
from ...types import Response


def _get_kwargs(
    *,
    body: PostTracesBody,
    x_api_key: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["x-api-key"] = x_api_key

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/traces",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[PostTracesResponse201]:
    if response.status_code == 201:
        response_201 = PostTracesResponse201.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[PostTracesResponse201]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostTracesBody,
    x_api_key: str,
) -> Response[PostTracesResponse201]:
    """
    Args:
        x_api_key (str):
        body (PostTracesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostTracesResponse201]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostTracesBody,
    x_api_key: str,
) -> Optional[PostTracesResponse201]:
    """
    Args:
        x_api_key (str):
        body (PostTracesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostTracesResponse201
    """

    return sync_detailed(
        client=client,
        body=body,
        x_api_key=x_api_key,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostTracesBody,
    x_api_key: str,
) -> Response[PostTracesResponse201]:
    """
    Args:
        x_api_key (str):
        body (PostTracesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[PostTracesResponse201]
    """

    kwargs = _get_kwargs(
        body=body,
        x_api_key=x_api_key,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    body: PostTracesBody,
    x_api_key: str,
) -> Optional[PostTracesResponse201]:
    """
    Args:
        x_api_key (str):
        body (PostTracesBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        PostTracesResponse201
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
            x_api_key=x_api_key,
        )
    ).parsed
