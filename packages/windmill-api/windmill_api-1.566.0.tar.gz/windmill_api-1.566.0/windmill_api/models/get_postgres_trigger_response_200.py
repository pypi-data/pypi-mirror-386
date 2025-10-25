import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_postgres_trigger_response_200_error_handler_args import (
        GetPostgresTriggerResponse200ErrorHandlerArgs,
    )
    from ..models.get_postgres_trigger_response_200_extra_perms import GetPostgresTriggerResponse200ExtraPerms
    from ..models.get_postgres_trigger_response_200_retry import GetPostgresTriggerResponse200Retry


T = TypeVar("T", bound="GetPostgresTriggerResponse200")


@_attrs_define
class GetPostgresTriggerResponse200:
    """
    Attributes:
        enabled (bool):
        postgres_resource_path (str):
        publication_name (str):
        replication_slot_name (str):
        path (str):
        script_path (str):
        email (str):
        extra_perms (GetPostgresTriggerResponse200ExtraPerms):
        workspace_id (str):
        edited_by (str):
        edited_at (datetime.datetime):
        is_flow (bool):
        server_id (Union[Unset, str]):
        error (Union[Unset, str]):
        last_server_ping (Union[Unset, datetime.datetime]):
        error_handler_path (Union[Unset, str]):
        error_handler_args (Union[Unset, GetPostgresTriggerResponse200ErrorHandlerArgs]): The arguments to pass to the
            script or flow
        retry (Union[Unset, GetPostgresTriggerResponse200Retry]):
    """

    enabled: bool
    postgres_resource_path: str
    publication_name: str
    replication_slot_name: str
    path: str
    script_path: str
    email: str
    extra_perms: "GetPostgresTriggerResponse200ExtraPerms"
    workspace_id: str
    edited_by: str
    edited_at: datetime.datetime
    is_flow: bool
    server_id: Union[Unset, str] = UNSET
    error: Union[Unset, str] = UNSET
    last_server_ping: Union[Unset, datetime.datetime] = UNSET
    error_handler_path: Union[Unset, str] = UNSET
    error_handler_args: Union[Unset, "GetPostgresTriggerResponse200ErrorHandlerArgs"] = UNSET
    retry: Union[Unset, "GetPostgresTriggerResponse200Retry"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        enabled = self.enabled
        postgres_resource_path = self.postgres_resource_path
        publication_name = self.publication_name
        replication_slot_name = self.replication_slot_name
        path = self.path
        script_path = self.script_path
        email = self.email
        extra_perms = self.extra_perms.to_dict()

        workspace_id = self.workspace_id
        edited_by = self.edited_by
        edited_at = self.edited_at.isoformat()

        is_flow = self.is_flow
        server_id = self.server_id
        error = self.error
        last_server_ping: Union[Unset, str] = UNSET
        if not isinstance(self.last_server_ping, Unset):
            last_server_ping = self.last_server_ping.isoformat()

        error_handler_path = self.error_handler_path
        error_handler_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.error_handler_args, Unset):
            error_handler_args = self.error_handler_args.to_dict()

        retry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.retry, Unset):
            retry = self.retry.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "enabled": enabled,
                "postgres_resource_path": postgres_resource_path,
                "publication_name": publication_name,
                "replication_slot_name": replication_slot_name,
                "path": path,
                "script_path": script_path,
                "email": email,
                "extra_perms": extra_perms,
                "workspace_id": workspace_id,
                "edited_by": edited_by,
                "edited_at": edited_at,
                "is_flow": is_flow,
            }
        )
        if server_id is not UNSET:
            field_dict["server_id"] = server_id
        if error is not UNSET:
            field_dict["error"] = error
        if last_server_ping is not UNSET:
            field_dict["last_server_ping"] = last_server_ping
        if error_handler_path is not UNSET:
            field_dict["error_handler_path"] = error_handler_path
        if error_handler_args is not UNSET:
            field_dict["error_handler_args"] = error_handler_args
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_postgres_trigger_response_200_error_handler_args import (
            GetPostgresTriggerResponse200ErrorHandlerArgs,
        )
        from ..models.get_postgres_trigger_response_200_extra_perms import GetPostgresTriggerResponse200ExtraPerms
        from ..models.get_postgres_trigger_response_200_retry import GetPostgresTriggerResponse200Retry

        d = src_dict.copy()
        enabled = d.pop("enabled")

        postgres_resource_path = d.pop("postgres_resource_path")

        publication_name = d.pop("publication_name")

        replication_slot_name = d.pop("replication_slot_name")

        path = d.pop("path")

        script_path = d.pop("script_path")

        email = d.pop("email")

        extra_perms = GetPostgresTriggerResponse200ExtraPerms.from_dict(d.pop("extra_perms"))

        workspace_id = d.pop("workspace_id")

        edited_by = d.pop("edited_by")

        edited_at = isoparse(d.pop("edited_at"))

        is_flow = d.pop("is_flow")

        server_id = d.pop("server_id", UNSET)

        error = d.pop("error", UNSET)

        _last_server_ping = d.pop("last_server_ping", UNSET)
        last_server_ping: Union[Unset, datetime.datetime]
        if isinstance(_last_server_ping, Unset):
            last_server_ping = UNSET
        else:
            last_server_ping = isoparse(_last_server_ping)

        error_handler_path = d.pop("error_handler_path", UNSET)

        _error_handler_args = d.pop("error_handler_args", UNSET)
        error_handler_args: Union[Unset, GetPostgresTriggerResponse200ErrorHandlerArgs]
        if isinstance(_error_handler_args, Unset):
            error_handler_args = UNSET
        else:
            error_handler_args = GetPostgresTriggerResponse200ErrorHandlerArgs.from_dict(_error_handler_args)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, GetPostgresTriggerResponse200Retry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = GetPostgresTriggerResponse200Retry.from_dict(_retry)

        get_postgres_trigger_response_200 = cls(
            enabled=enabled,
            postgres_resource_path=postgres_resource_path,
            publication_name=publication_name,
            replication_slot_name=replication_slot_name,
            path=path,
            script_path=script_path,
            email=email,
            extra_perms=extra_perms,
            workspace_id=workspace_id,
            edited_by=edited_by,
            edited_at=edited_at,
            is_flow=is_flow,
            server_id=server_id,
            error=error,
            last_server_ping=last_server_ping,
            error_handler_path=error_handler_path,
            error_handler_args=error_handler_args,
            retry=retry,
        )

        get_postgres_trigger_response_200.additional_properties = d
        return get_postgres_trigger_response_200

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
