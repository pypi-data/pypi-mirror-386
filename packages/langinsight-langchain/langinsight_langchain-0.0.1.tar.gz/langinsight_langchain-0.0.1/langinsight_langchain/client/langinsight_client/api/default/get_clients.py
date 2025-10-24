from http import HTTPStatus
from typing import Any, Optional, Union
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_clients_response_200_item import GetClientsResponse200Item
from ...types import UNSET, Response


def _get_kwargs(
    *,
    filter_project_id_in: list[UUID],
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_filter_project_id_in = []
    for filter_project_id_in_item_data in filter_project_id_in:
        filter_project_id_in_item = str(filter_project_id_in_item_data)
        json_filter_project_id_in.append(filter_project_id_in_item)

    params["filter.projectId.$in"] = json_filter_project_id_in

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/clients",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[list["GetClientsResponse200Item"]]:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = GetClientsResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[list["GetClientsResponse200Item"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_project_id_in: list[UUID],
) -> Response[list["GetClientsResponse200Item"]]:
    """
    Args:
        filter_project_id_in (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetClientsResponse200Item']]
    """

    kwargs = _get_kwargs(
        filter_project_id_in=filter_project_id_in,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_project_id_in: list[UUID],
) -> Optional[list["GetClientsResponse200Item"]]:
    """
    Args:
        filter_project_id_in (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetClientsResponse200Item']
    """

    return sync_detailed(
        client=client,
        filter_project_id_in=filter_project_id_in,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_project_id_in: list[UUID],
) -> Response[list["GetClientsResponse200Item"]]:
    """
    Args:
        filter_project_id_in (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list['GetClientsResponse200Item']]
    """

    kwargs = _get_kwargs(
        filter_project_id_in=filter_project_id_in,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    filter_project_id_in: list[UUID],
) -> Optional[list["GetClientsResponse200Item"]]:
    """
    Args:
        filter_project_id_in (list[UUID]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list['GetClientsResponse200Item']
    """

    return (
        await asyncio_detailed(
            client=client,
            filter_project_id_in=filter_project_id_in,
        )
    ).parsed
