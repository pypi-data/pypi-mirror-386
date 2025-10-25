from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_kafka_triggers_response_200_item import ListKafkaTriggersResponse200Item
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    *,
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    path: Union[Unset, None, str] = UNSET,
    is_flow: Union[Unset, None, bool] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["page"] = page

    params["per_page"] = per_page

    params["path"] = path

    params["is_flow"] = is_flow

    params["path_start"] = path_start

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/w/{workspace}/kafka_triggers/list".format(
            workspace=workspace,
        ),
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["ListKafkaTriggersResponse200Item"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ListKafkaTriggersResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["ListKafkaTriggersResponse200Item"]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    path: Union[Unset, None, str] = UNSET,
    is_flow: Union[Unset, None, bool] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Response[List["ListKafkaTriggersResponse200Item"]]:
    """list kafka triggers

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        path (Union[Unset, None, str]):
        is_flow (Union[Unset, None, bool]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListKafkaTriggersResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        path=path,
        is_flow=is_flow,
        path_start=path_start,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    path: Union[Unset, None, str] = UNSET,
    is_flow: Union[Unset, None, bool] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListKafkaTriggersResponse200Item"]]:
    """list kafka triggers

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        path (Union[Unset, None, str]):
        is_flow (Union[Unset, None, bool]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListKafkaTriggersResponse200Item']
    """

    return sync_detailed(
        workspace=workspace,
        client=client,
        page=page,
        per_page=per_page,
        path=path,
        is_flow=is_flow,
        path_start=path_start,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    path: Union[Unset, None, str] = UNSET,
    is_flow: Union[Unset, None, bool] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Response[List["ListKafkaTriggersResponse200Item"]]:
    """list kafka triggers

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        path (Union[Unset, None, str]):
        is_flow (Union[Unset, None, bool]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListKafkaTriggersResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        path=path,
        is_flow=is_flow,
        path_start=path_start,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    path: Union[Unset, None, str] = UNSET,
    is_flow: Union[Unset, None, bool] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListKafkaTriggersResponse200Item"]]:
    """list kafka triggers

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        path (Union[Unset, None, str]):
        is_flow (Union[Unset, None, bool]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListKafkaTriggersResponse200Item']
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            client=client,
            page=page,
            per_page=per_page,
            path=path,
            is_flow=is_flow,
            path_start=path_start,
        )
    ).parsed
