from http import HTTPStatus
from typing import Any, Dict, List, Optional, Union

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.list_scripts_response_200_item import ListScriptsResponse200Item
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    *,
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    order_desc: Union[Unset, None, bool] = UNSET,
    created_by: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
    path_exact: Union[Unset, None, str] = UNSET,
    first_parent_hash: Union[Unset, None, str] = UNSET,
    last_parent_hash: Union[Unset, None, str] = UNSET,
    parent_hash: Union[Unset, None, str] = UNSET,
    show_archived: Union[Unset, None, bool] = UNSET,
    include_without_main: Union[Unset, None, bool] = UNSET,
    include_draft_only: Union[Unset, None, bool] = UNSET,
    is_template: Union[Unset, None, bool] = UNSET,
    kinds: Union[Unset, None, str] = UNSET,
    starred_only: Union[Unset, None, bool] = UNSET,
    with_deployment_msg: Union[Unset, None, bool] = UNSET,
    languages: Union[Unset, None, str] = UNSET,
) -> Dict[str, Any]:
    pass

    params: Dict[str, Any] = {}
    params["page"] = page

    params["per_page"] = per_page

    params["order_desc"] = order_desc

    params["created_by"] = created_by

    params["path_start"] = path_start

    params["path_exact"] = path_exact

    params["first_parent_hash"] = first_parent_hash

    params["last_parent_hash"] = last_parent_hash

    params["parent_hash"] = parent_hash

    params["show_archived"] = show_archived

    params["include_without_main"] = include_without_main

    params["include_draft_only"] = include_draft_only

    params["is_template"] = is_template

    params["kinds"] = kinds

    params["starred_only"] = starred_only

    params["with_deployment_msg"] = with_deployment_msg

    params["languages"] = languages

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    return {
        "method": "get",
        "url": "/w/{workspace}/scripts/list".format(
            workspace=workspace,
        ),
        "params": params,
    }


def _parse_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Optional[List["ListScriptsResponse200Item"]]:
    if response.status_code == HTTPStatus.OK:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = ListScriptsResponse200Item.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200
    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: Union[AuthenticatedClient, Client], response: httpx.Response
) -> Response[List["ListScriptsResponse200Item"]]:
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
    order_desc: Union[Unset, None, bool] = UNSET,
    created_by: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
    path_exact: Union[Unset, None, str] = UNSET,
    first_parent_hash: Union[Unset, None, str] = UNSET,
    last_parent_hash: Union[Unset, None, str] = UNSET,
    parent_hash: Union[Unset, None, str] = UNSET,
    show_archived: Union[Unset, None, bool] = UNSET,
    include_without_main: Union[Unset, None, bool] = UNSET,
    include_draft_only: Union[Unset, None, bool] = UNSET,
    is_template: Union[Unset, None, bool] = UNSET,
    kinds: Union[Unset, None, str] = UNSET,
    starred_only: Union[Unset, None, bool] = UNSET,
    with_deployment_msg: Union[Unset, None, bool] = UNSET,
    languages: Union[Unset, None, str] = UNSET,
) -> Response[List["ListScriptsResponse200Item"]]:
    """list all scripts

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        order_desc (Union[Unset, None, bool]):
        created_by (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):
        path_exact (Union[Unset, None, str]):
        first_parent_hash (Union[Unset, None, str]):
        last_parent_hash (Union[Unset, None, str]):
        parent_hash (Union[Unset, None, str]):
        show_archived (Union[Unset, None, bool]):
        include_without_main (Union[Unset, None, bool]):
        include_draft_only (Union[Unset, None, bool]):
        is_template (Union[Unset, None, bool]):
        kinds (Union[Unset, None, str]):
        starred_only (Union[Unset, None, bool]):
        with_deployment_msg (Union[Unset, None, bool]):
        languages (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListScriptsResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        order_desc=order_desc,
        created_by=created_by,
        path_start=path_start,
        path_exact=path_exact,
        first_parent_hash=first_parent_hash,
        last_parent_hash=last_parent_hash,
        parent_hash=parent_hash,
        show_archived=show_archived,
        include_without_main=include_without_main,
        include_draft_only=include_draft_only,
        is_template=is_template,
        kinds=kinds,
        starred_only=starred_only,
        with_deployment_msg=with_deployment_msg,
        languages=languages,
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
    order_desc: Union[Unset, None, bool] = UNSET,
    created_by: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
    path_exact: Union[Unset, None, str] = UNSET,
    first_parent_hash: Union[Unset, None, str] = UNSET,
    last_parent_hash: Union[Unset, None, str] = UNSET,
    parent_hash: Union[Unset, None, str] = UNSET,
    show_archived: Union[Unset, None, bool] = UNSET,
    include_without_main: Union[Unset, None, bool] = UNSET,
    include_draft_only: Union[Unset, None, bool] = UNSET,
    is_template: Union[Unset, None, bool] = UNSET,
    kinds: Union[Unset, None, str] = UNSET,
    starred_only: Union[Unset, None, bool] = UNSET,
    with_deployment_msg: Union[Unset, None, bool] = UNSET,
    languages: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListScriptsResponse200Item"]]:
    """list all scripts

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        order_desc (Union[Unset, None, bool]):
        created_by (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):
        path_exact (Union[Unset, None, str]):
        first_parent_hash (Union[Unset, None, str]):
        last_parent_hash (Union[Unset, None, str]):
        parent_hash (Union[Unset, None, str]):
        show_archived (Union[Unset, None, bool]):
        include_without_main (Union[Unset, None, bool]):
        include_draft_only (Union[Unset, None, bool]):
        is_template (Union[Unset, None, bool]):
        kinds (Union[Unset, None, str]):
        starred_only (Union[Unset, None, bool]):
        with_deployment_msg (Union[Unset, None, bool]):
        languages (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListScriptsResponse200Item']
    """

    return sync_detailed(
        workspace=workspace,
        client=client,
        page=page,
        per_page=per_page,
        order_desc=order_desc,
        created_by=created_by,
        path_start=path_start,
        path_exact=path_exact,
        first_parent_hash=first_parent_hash,
        last_parent_hash=last_parent_hash,
        parent_hash=parent_hash,
        show_archived=show_archived,
        include_without_main=include_without_main,
        include_draft_only=include_draft_only,
        is_template=is_template,
        kinds=kinds,
        starred_only=starred_only,
        with_deployment_msg=with_deployment_msg,
        languages=languages,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    order_desc: Union[Unset, None, bool] = UNSET,
    created_by: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
    path_exact: Union[Unset, None, str] = UNSET,
    first_parent_hash: Union[Unset, None, str] = UNSET,
    last_parent_hash: Union[Unset, None, str] = UNSET,
    parent_hash: Union[Unset, None, str] = UNSET,
    show_archived: Union[Unset, None, bool] = UNSET,
    include_without_main: Union[Unset, None, bool] = UNSET,
    include_draft_only: Union[Unset, None, bool] = UNSET,
    is_template: Union[Unset, None, bool] = UNSET,
    kinds: Union[Unset, None, str] = UNSET,
    starred_only: Union[Unset, None, bool] = UNSET,
    with_deployment_msg: Union[Unset, None, bool] = UNSET,
    languages: Union[Unset, None, str] = UNSET,
) -> Response[List["ListScriptsResponse200Item"]]:
    """list all scripts

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        order_desc (Union[Unset, None, bool]):
        created_by (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):
        path_exact (Union[Unset, None, str]):
        first_parent_hash (Union[Unset, None, str]):
        last_parent_hash (Union[Unset, None, str]):
        parent_hash (Union[Unset, None, str]):
        show_archived (Union[Unset, None, bool]):
        include_without_main (Union[Unset, None, bool]):
        include_draft_only (Union[Unset, None, bool]):
        is_template (Union[Unset, None, bool]):
        kinds (Union[Unset, None, str]):
        starred_only (Union[Unset, None, bool]):
        with_deployment_msg (Union[Unset, None, bool]):
        languages (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[List['ListScriptsResponse200Item']]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        page=page,
        per_page=per_page,
        order_desc=order_desc,
        created_by=created_by,
        path_start=path_start,
        path_exact=path_exact,
        first_parent_hash=first_parent_hash,
        last_parent_hash=last_parent_hash,
        parent_hash=parent_hash,
        show_archived=show_archived,
        include_without_main=include_without_main,
        include_draft_only=include_draft_only,
        is_template=is_template,
        kinds=kinds,
        starred_only=starred_only,
        with_deployment_msg=with_deployment_msg,
        languages=languages,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    *,
    client: Union[AuthenticatedClient, Client],
    page: Union[Unset, None, int] = UNSET,
    per_page: Union[Unset, None, int] = UNSET,
    order_desc: Union[Unset, None, bool] = UNSET,
    created_by: Union[Unset, None, str] = UNSET,
    path_start: Union[Unset, None, str] = UNSET,
    path_exact: Union[Unset, None, str] = UNSET,
    first_parent_hash: Union[Unset, None, str] = UNSET,
    last_parent_hash: Union[Unset, None, str] = UNSET,
    parent_hash: Union[Unset, None, str] = UNSET,
    show_archived: Union[Unset, None, bool] = UNSET,
    include_without_main: Union[Unset, None, bool] = UNSET,
    include_draft_only: Union[Unset, None, bool] = UNSET,
    is_template: Union[Unset, None, bool] = UNSET,
    kinds: Union[Unset, None, str] = UNSET,
    starred_only: Union[Unset, None, bool] = UNSET,
    with_deployment_msg: Union[Unset, None, bool] = UNSET,
    languages: Union[Unset, None, str] = UNSET,
) -> Optional[List["ListScriptsResponse200Item"]]:
    """list all scripts

    Args:
        workspace (str):
        page (Union[Unset, None, int]):
        per_page (Union[Unset, None, int]):
        order_desc (Union[Unset, None, bool]):
        created_by (Union[Unset, None, str]):
        path_start (Union[Unset, None, str]):
        path_exact (Union[Unset, None, str]):
        first_parent_hash (Union[Unset, None, str]):
        last_parent_hash (Union[Unset, None, str]):
        parent_hash (Union[Unset, None, str]):
        show_archived (Union[Unset, None, bool]):
        include_without_main (Union[Unset, None, bool]):
        include_draft_only (Union[Unset, None, bool]):
        is_template (Union[Unset, None, bool]):
        kinds (Union[Unset, None, str]):
        starred_only (Union[Unset, None, bool]):
        with_deployment_msg (Union[Unset, None, bool]):
        languages (Union[Unset, None, str]):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        List['ListScriptsResponse200Item']
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            client=client,
            page=page,
            per_page=per_page,
            order_desc=order_desc,
            created_by=created_by,
            path_start=path_start,
            path_exact=path_exact,
            first_parent_hash=first_parent_hash,
            last_parent_hash=last_parent_hash,
            parent_hash=parent_hash,
            show_archived=show_archived,
            include_without_main=include_without_main,
            include_draft_only=include_draft_only,
            is_template=is_template,
            kinds=kinds,
            starred_only=starred_only,
            with_deployment_msg=with_deployment_msg,
            languages=languages,
        )
    ).parsed
