from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.run_script_preview_json_body import RunScriptPreviewJsonBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    *,
    json_body: RunScriptPreviewJsonBody,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["include_header"] = include_header

    params["invisible_to_owner"] = invisible_to_owner

    params["job_id"] = job_id

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/w/{workspace}/jobs/run/preview".format(
            workspace=workspace,
        ),
        "json": json_json_body,
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
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RunScriptPreviewJsonBody,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
) -> Response[Any]:
    """run script preview

    Args:
        workspace (str):
        include_header (Union[Unset, None, str]):
        invisible_to_owner (Union[Unset, None, bool]):
        job_id (Union[Unset, None, str]):
        json_body (RunScriptPreviewJsonBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        json_body=json_body,
        include_header=include_header,
        invisible_to_owner=invisible_to_owner,
        job_id=job_id,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RunScriptPreviewJsonBody,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
) -> Response[Any]:
    """run script preview

    Args:
        workspace (str):
        include_header (Union[Unset, None, str]):
        invisible_to_owner (Union[Unset, None, bool]):
        job_id (Union[Unset, None, str]):
        json_body (RunScriptPreviewJsonBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        json_body=json_body,
        include_header=include_header,
        invisible_to_owner=invisible_to_owner,
        job_id=job_id,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
