from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_top_hub_scripts_response_200 import GetTopHubScriptsResponse200
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    limit: Union[Unset, None, float] = UNSET,
    app: Union[Unset, None, str] = UNSET,
    kind: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["limit"] = limit

    params["app"] = app

    params["kind"] = kind

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/scripts/hub/top",
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[GetTopHubScriptsResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = GetTopHubScriptsResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[GetTopHubScriptsResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, None, float] = UNSET,
    app: Union[Unset, None, str] = UNSET,
    kind: Union[Unset, None, str] = UNSET,
) -> Response[GetTopHubScriptsResponse200]:
    """get top hub scripts

    Args:
        limit (Union[Unset, None, float]):
        app (Union[Unset, None, str]):
        kind (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetTopHubScriptsResponse200]
    """

    kwargs = _get_kwargs(
        limit=limit,
        app=app,
        kind=kind,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, None, float] = UNSET,
    app: Union[Unset, None, str] = UNSET,
    kind: Union[Unset, None, str] = UNSET,
) -> Optional[GetTopHubScriptsResponse200]:
    """get top hub scripts

    Args:
        limit (Union[Unset, None, float]):
        app (Union[Unset, None, str]):
        kind (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetTopHubScriptsResponse200
    """

    return sync_detailed(
        client=client,
        limit=limit,
        app=app,
        kind=kind,
    ).parsed


async def asyncio_detailed(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, None, float] = UNSET,
    app: Union[Unset, None, str] = UNSET,
    kind: Union[Unset, None, str] = UNSET,
) -> Response[GetTopHubScriptsResponse200]:
    """get top hub scripts

    Args:
        limit (Union[Unset, None, float]):
        app (Union[Unset, None, str]):
        kind (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[GetTopHubScriptsResponse200]
    """

    kwargs = _get_kwargs(
        limit=limit,
        app=app,
        kind=kind,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: Union[AuthenticatedClient, Client],
    limit: Union[Unset, None, float] = UNSET,
    app: Union[Unset, None, str] = UNSET,
    kind: Union[Unset, None, str] = UNSET,
) -> Optional[GetTopHubScriptsResponse200]:
    """get top hub scripts

    Args:
        limit (Union[Unset, None, float]):
        app (Union[Unset, None, str]):
        kind (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        GetTopHubScriptsResponse200
    """

    return (
        await asyncio_detailed(
            client=client,
            limit=limit,
            app=app,
            kind=kind,
        )
    ).parsed
