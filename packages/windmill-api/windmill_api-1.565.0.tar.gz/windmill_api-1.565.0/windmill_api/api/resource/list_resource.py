from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_resource_response_200_item import ListResourceResponse200Item
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    *,
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    resource_type: Union[Unset, None, str] = UNSET,
    resource_type_exclude: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["page"] = page

    params["per_page"] = per_page

    params["resource_type"] = resource_type

    params["resource_type_exclude"] = resource_type_exclude

    params["path_start"] = path_start

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/w/{workspace}/resources/list".format(
            workspace=workspace,
        ),
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["ListResourceResponse200Item"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ListResourceResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["ListResourceResponse200Item"]]:
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
    resource_type: Union[Unset, None, str] = UNSET,
    resource_type_exclude: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Response[List["ListResourceResponse200Item"]]:
    """list resources

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        resource_type (Union[Unset, None, str]):
        resource_type_exclude (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListResourceResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        resource_type=resource_type,
        resource_type_exclude=resource_type_exclude,
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
    resource_type: Union[Unset, None, str] = UNSET,
    resource_type_exclude: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListResourceResponse200Item"]]:
    """list resources

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        resource_type (Union[Unset, None, str]):
        resource_type_exclude (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListResourceResponse200Item']
    """

    return sync_detailed(
        workspace=workspace,
        client=client,
        page=page,
        per_page=per_page,
        resource_type=resource_type,
        resource_type_exclude=resource_type_exclude,
        path_start=path_start,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    resource_type: Union[Unset, None, str] = UNSET,
    resource_type_exclude: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Response[List["ListResourceResponse200Item"]]:
    """list resources

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        resource_type (Union[Unset, None, str]):
        resource_type_exclude (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListResourceResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        resource_type=resource_type,
        resource_type_exclude=resource_type_exclude,
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
    resource_type: Union[Unset, None, str] = UNSET,
    resource_type_exclude: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListResourceResponse200Item"]]:
    """list resources

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        resource_type (Union[Unset, None, str]):
        resource_type_exclude (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListResourceResponse200Item']
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            client=client,
            page=page,
            per_page=per_page,
            resource_type=resource_type,
            resource_type_exclude=resource_type_exclude,
            path_start=path_start,
        )
    ).parsed
