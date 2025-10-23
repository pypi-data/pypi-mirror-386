from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.run_wait_result_script_by_path_json_body import RunWaitResultScriptByPathJsonBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    path: str,
    *,
    json_body: RunWaitResultScriptByPathJsonBody,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    cache_ttl: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["parent_job"] = parent_job

    params["tag"] = tag

    params["cache_ttl"] = cache_ttl

    params["job_id"] = job_id

    params["include_header"] = include_header

    params["queue_limit"] = queue_limit

    params["skip_preprocessor"] = skip_preprocessor

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/w/{workspace}/jobs/run_wait_result/p/{path}".format(
            workspace=workspace,
            path=path,
        ),
        "json": json_json_body,
        "params": params,
    }


def _parse_response(*, client: Union[AuthenticatedClient, Client], response: httpx.Response) -> Optional[Any]:
    if response.status_code == HTTPStatus.OK:
        return None
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
    json_body: RunWaitResultScriptByPathJsonBody,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    cache_ttl: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
) -> Response[Any]:
    """run script by path

    Args:
        workspace (str):
        path (str):
        parent_job (Union[Unset, None, str]):
        tag (Union[Unset, None, str]):
        cache_ttl (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        include_header (Union[Unset, None, str]):
        queue_limit (Union[Unset, None, str]):
        skip_preprocessor (Union[Unset, None, bool]):
        json_body (RunWaitResultScriptByPathJsonBody): The arguments to pass to the script or flow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        path=path,
        json_body=json_body,
        parent_job=parent_job,
        tag=tag,
        cache_ttl=cache_ttl,
        job_id=job_id,
        include_header=include_header,
        queue_limit=queue_limit,
        skip_preprocessor=skip_preprocessor,
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
    json_body: RunWaitResultScriptByPathJsonBody,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    cache_ttl: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    queue_limit: Union[Unset, None, str] = UNSET,
    skip_preprocessor: Union[Unset, None, bool] = UNSET,
) -> Response[Any]:
    """run script by path

    Args:
        workspace (str):
        path (str):
        parent_job (Union[Unset, None, str]):
        tag (Union[Unset, None, str]):
        cache_ttl (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        include_header (Union[Unset, None, str]):
        queue_limit (Union[Unset, None, str]):
        skip_preprocessor (Union[Unset, None, bool]):
        json_body (RunWaitResultScriptByPathJsonBody): The arguments to pass to the script or flow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        path=path,
        json_body=json_body,
        parent_job=parent_job,
        tag=tag,
        cache_ttl=cache_ttl,
        job_id=job_id,
        include_header=include_header,
        queue_limit=queue_limit,
        skip_preprocessor=skip_preprocessor,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
