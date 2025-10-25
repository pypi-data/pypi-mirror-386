from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    path: str,
    *,
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    payload: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
    memory_id: Union[Unset, None, str] = UNSET,
    poll_delay_ms: Union[Unset, None, int] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["include_header"] = include_header

    params["queue_limit"] = queue_limit

    params["payload"] = payload

    params["job_id"] = job_id

    params["skip_preprocessor"] = skip_preprocessor

    params["memory_id"] = memory_id

    params["poll_delay_ms"] = poll_delay_ms

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/w/{workspace}/jobs/run_and_stream/f/{path}".format(
            workspace=workspace,
            path=path,
        ),
        "params": params,
    }


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Any]:
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    path: str,
    *,
    client: Union[AuthenticatedClient, Client],
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    payload: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
    memory_id: Union[Unset, None, str] = UNSET,
    poll_delay_ms: Union[Unset, None, int] = UNSET,
) -> Response[Any]:
    """run flow by path with GET and stream updates via SSE

    Args:
        workspace (str):
        path (str):
        include_header (Union[Unset, None, str]):
        queue_limit (Union[Unset, None, str]):
        payload (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        skip_preprocessor (Union[Unset, None, bool]):
        memory_id (Union[Unset, None, str]):
        poll_delay_ms (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        path=path,
        include_header=include_header,
        queue_limit=queue_limit,
        payload=payload,
        job_id=job_id,
        skip_preprocessor=skip_preprocessor,
        memory_id=memory_id,
        poll_delay_ms=poll_delay_ms,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    workspace: str,
    path: str,
    *,
    client: Union[AuthenticatedClient, Client],
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    payload: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
    memory_id: Union[Unset, None, str] = UNSET,
    poll_delay_ms: Union[Unset, None, int] = UNSET,
) -> Response[Any]:
    """run flow by path with GET and stream updates via SSE

    Args:
        workspace (str):
        path (str):
        include_header (Union[Unset, None, str]):
        queue_limit (Union[Unset, None, str]):
        payload (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        skip_preprocessor (Union[Unset, None, bool]):
        memory_id (Union[Unset, None, str]):
        poll_delay_ms (Union[Unset, None, int]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        path=path,
        include_header=include_header,
        queue_limit=queue_limit,
        payload=payload,
        job_id=job_id,
        skip_preprocessor=skip_preprocessor,
        memory_id=memory_id,
        poll_delay_ms=poll_delay_ms,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
