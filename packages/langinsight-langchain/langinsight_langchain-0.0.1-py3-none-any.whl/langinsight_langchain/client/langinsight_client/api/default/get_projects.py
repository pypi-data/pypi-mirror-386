from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_projects_response_200_item import GetProjectsResponse200Item
from ...types import UNSET, Response


def _get_kwargs(
    *,
    filter_client_id_eq: UUID,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_filter_client_id_eq = str(filter_client_id_eq)
    params["filter.clientId.$eq"] = json_filter_client_id_eq

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/projects",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["GetProjectsResponse200Item"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetProjectsResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["GetProjectsResponse200Item"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_client_id_eq: UUID,
) -> Response[list["GetProjectsResponse200Item"]]:
    """
    Args:
        filter_client_id_eq (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetProjectsResponse200Item']]
    """

    kwargs = _get_kwargs(
        filter_client_id_eq=filter_client_id_eq,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_client_id_eq: UUID,
) -> Optional[list["GetProjectsResponse200Item"]]:
    """
    Args:
        filter_client_id_eq (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetProjectsResponse200Item']
    """

    return sync_detailed(
        client=client,
        filter_client_id_eq=filter_client_id_eq,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_client_id_eq: UUID,
) -> Response[list["GetProjectsResponse200Item"]]:
    """
    Args:
        filter_client_id_eq (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetProjectsResponse200Item']]
    """

    kwargs = _get_kwargs(
        filter_client_id_eq=filter_client_id_eq,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_client_id_eq: UUID,
) -> Optional[list["GetProjectsResponse200Item"]]:
    """
    Args:
        filter_client_id_eq (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetProjectsResponse200Item']
    """

    return (
        await asyncio_detailed(
            client=client,
            filter_client_id_eq=filter_client_id_eq,
        )
    ).parsed
