from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_workers_response_200_item import ListWorkersResponse200Item
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    ping_since: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["page"] = page

    params["per_page"] = per_page

    params["ping_since"] = ping_since

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/workers/list",
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["ListWorkersResponse200Item"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ListWorkersResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["ListWorkersResponse200Item"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    ping_since: Union[Unset, None, int] = UNSET,
) -> Response[List["ListWorkersResponse200Item"]]:
    """list workers

    Args:
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        ping_since (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListWorkersResponse200Item']]
    """

    kwargs = _get_kwargs(
        page=page,
        per_page=per_page,
        ping_since=ping_since,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    ping_since: Union[Unset, None, int] = UNSET,
) -> Optional[List["ListWorkersResponse200Item"]]:
    """list workers

    Args:
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        ping_since (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListWorkersResponse200Item']
    """

    return sync_detailed(
        client=client,
        page=page,
        per_page=per_page,
        ping_since=ping_since,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    ping_since: Union[Unset, None, int] = UNSET,
) -> Response[List["ListWorkersResponse200Item"]]:
    """list workers

    Args:
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        ping_since (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListWorkersResponse200Item']]
    """

    kwargs = _get_kwargs(
        page=page,
        per_page=per_page,
        ping_since=ping_since,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    ping_since: Union[Unset, None, int] = UNSET,
) -> Optional[List["ListWorkersResponse200Item"]]:
    """list workers

    Args:
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        ping_since (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListWorkersResponse200Item']
    """

    return (
        await asyncio_detailed(
            client=client,
            page=page,
            per_page=per_page,
            ping_since=ping_since,
        )
    ).parsed
