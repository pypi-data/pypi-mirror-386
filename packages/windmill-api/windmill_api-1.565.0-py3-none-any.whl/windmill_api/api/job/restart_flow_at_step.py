import datetime
from http import HTTPStatus
from typing import Any, Dict, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.restart_flow_at_step_json_body import RestartFlowAtStepJsonBody
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    id: str,
    step_id: str,
    branch_or_iteration_n: int,
    *,
    json_body: RestartFlowAtStepJsonBody,
    scheduled_for: Union[Unset, None, datetime.datetime] = UNSET,
    scheduled_in_secs: Union[Unset, None, int] = UNSET,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    json_scheduled_for: Union[Unset, None, str] = UNSET
    if not isinstance(scheduled_for, Unset):
        json_scheduled_for = scheduled_for.isoformat() if scheduled_for else None

    params["scheduled_for"] = json_scheduled_for

    params["scheduled_in_secs"] = scheduled_in_secs

    params["parent_job"] = parent_job

    params["tag"] = tag

    params["job_id"] = job_id

    params["include_header"] = include_header

    params["invisible_to_owner"] = invisible_to_owner

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    json_json_body = json_body.to_dict()

    return {
        "method": "post",
        "url": "/w/{workspace}/jobs/restart/f/{id}/from/{step_id}/{branch_or_iteration_n}".format(
            workspace=workspace,
            id=id,
            step_id=step_id,
            branch_or_iteration_n=branch_or_iteration_n,
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
    id: str,
    step_id: str,
    branch_or_iteration_n: int,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RestartFlowAtStepJsonBody,
    scheduled_for: Union[Unset, None, datetime.datetime] = UNSET,
    scheduled_in_secs: Union[Unset, None, int] = UNSET,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
) -> Response[Any]:
    """restart a completed flow at a given step

    Args:
        workspace (str):
        id (str):
        step_id (str):
        branch_or_iteration_n (int):
        scheduled_for (Union[Unset, None, datetime.datetime]):
        scheduled_in_secs (Union[Unset, None, int]):
        parent_job (Union[Unset, None, str]):
        tag (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        include_header (Union[Unset, None, str]):
        invisible_to_owner (Union[Unset, None, bool]):
        json_body (RestartFlowAtStepJsonBody): The arguments to pass to the script or flow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        id=id,
        step_id=step_id,
        branch_or_iteration_n=branch_or_iteration_n,
        json_body=json_body,
        scheduled_for=scheduled_for,
        scheduled_in_secs=scheduled_in_secs,
        parent_job=parent_job,
        tag=tag,
        job_id=job_id,
        include_header=include_header,
        invisible_to_owner=invisible_to_owner,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    workspace: str,
    id: str,
    step_id: str,
    branch_or_iteration_n: int,
    *,
    client: Union[AuthenticatedClient, Client],
    json_body: RestartFlowAtStepJsonBody,
    scheduled_for: Union[Unset, None, datetime.datetime] = UNSET,
    scheduled_in_secs: Union[Unset, None, int] = UNSET,
    parent_job: Union[Unset, None, str] = UNSET,
    tag: Union[Unset, None, str] = UNSET,
    job_id: Union[Unset, None, str] = UNSET,
    include_header: Union[Unset, None, str] = UNSET,
    invisible_to_owner: Union[Unset, None, bool] = UNSET,
) -> Response[Any]:
    """restart a completed flow at a given step

    Args:
        workspace (str):
        id (str):
        step_id (str):
        branch_or_iteration_n (int):
        scheduled_for (Union[Unset, None, datetime.datetime]):
        scheduled_in_secs (Union[Unset, None, int]):
        parent_job (Union[Unset, None, str]):
        tag (Union[Unset, None, str]):
        job_id (Union[Unset, None, str]):
        include_header (Union[Unset, None, str]):
        invisible_to_owner (Union[Unset, None, bool]):
        json_body (RestartFlowAtStepJsonBody): The arguments to pass to the script or flow

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        id=id,
        step_id=step_id,
        branch_or_iteration_n=branch_or_iteration_n,
        json_body=json_body,
        scheduled_for=scheduled_for,
        scheduled_in_secs=scheduled_in_secs,
        parent_job=parent_job,
        tag=tag,
        job_id=job_id,
        include_header=include_header,
        invisible_to_owner=invisible_to_owner,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
