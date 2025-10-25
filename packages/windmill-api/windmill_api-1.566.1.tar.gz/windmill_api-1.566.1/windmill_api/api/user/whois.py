from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.whois_response_200 import WhoisResponse200
from ...types import Response


def _get_kwargs(
    workspace: str,
    username: str,
) -> Dict[str, Any]:
    pass

    return {
        "method": "get",
        "url": "/w/{workspace}/users/whois/{username}".format(
            workspace=workspace,
            username=username,
        ),
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[WhoisResponse200]:
    if response.status_code == HTTPStatus.OK:
        response_200 = WhoisResponse200.from_dict(response.json())

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[WhoisResponse200]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    username: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[WhoisResponse200]:
    """whois

    Args:
        workspace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WhoisResponse200]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        username=username,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    username: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[WhoisResponse200]:
    """whois

    Args:
        workspace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WhoisResponse200
    """

    return sync_detailed(
        workspace=workspace,
        username=username,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    username: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Response[WhoisResponse200]:
    """whois

    Args:
        workspace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WhoisResponse200]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        username=username,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    username: str,
    *,
    client: Union[AuthenticatedClient, Client],
) -> Optional[WhoisResponse200]:
    """whois

    Args:
        workspace (str):
        username (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WhoisResponse200
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            username=username,
            client=client,
        )
    ).parsed
