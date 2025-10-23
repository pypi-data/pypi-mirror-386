import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_resource_response_200_extra_perms import GetResourceResponse200ExtraPerms


T = TypeVar("T", bound="GetResourceResponse200")


@_attrs_define
class GetResourceResponse200:
    """
    Attributes:
        path (str):
        resource_type (str):
        is_oauth (bool):
        workspace_id (Union[Unset, str]):
        description (Union[Unset, str]):
        value (Union[Unset, Any]):
        extra_perms (Union[Unset, GetResourceResponse200ExtraPerms]):
        created_by (Union[Unset, str]):
        edited_at (Union[Unset, datetime.datetime]):
    """

    path: str
    resource_type: str
    is_oauth: bool
    workspace_id: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    value: Union[Unset, Any] = UNSET
    extra_perms: Union[Unset, "GetResourceResponse200ExtraPerms"] = UNSET
    created_by: Union[Unset, str] = UNSET
    edited_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        resource_type = self.resource_type
        is_oauth = self.is_oauth
        workspace_id = self.workspace_id
        description = self.description
        value = self.value
        extra_perms: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.extra_perms, Unset):
            extra_perms = self.extra_perms.to_dict()

        created_by = self.created_by
        edited_at: Union[Unset, str] = UNSET
        if not isinstance(self.edited_at, Unset):
            edited_at = self.edited_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "resource_type": resource_type,
                "is_oauth": is_oauth,
            }
        )
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if description is not UNSET:
            field_dict["description"] = description
        if value is not UNSET:
            field_dict["value"] = value
        if extra_perms is not UNSET:
            field_dict["extra_perms"] = extra_perms
        if created_by is not UNSET:
            field_dict["created_by"] = created_by
        if edited_at is not UNSET:
            field_dict["edited_at"] = edited_at

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_resource_response_200_extra_perms import GetResourceResponse200ExtraPerms

        d = src_dict.copy()
        path = d.pop("path")

        resource_type = d.pop("resource_type")

        is_oauth = d.pop("is_oauth")

        workspace_id = d.pop("workspace_id", UNSET)

        description = d.pop("description", UNSET)

        value = d.pop("value", UNSET)

        _extra_perms = d.pop("extra_perms", UNSET)
        extra_perms: Union[Unset, GetResourceResponse200ExtraPerms]
        if isinstance(_extra_perms, Unset):
            extra_perms = UNSET
        else:
            extra_perms = GetResourceResponse200ExtraPerms.from_dict(_extra_perms)

        created_by = d.pop("created_by", UNSET)

        _edited_at = d.pop("edited_at", UNSET)
        edited_at: Union[Unset, datetime.datetime]
        if isinstance(_edited_at, Unset):
            edited_at = UNSET
        else:
            edited_at = isoparse(_edited_at)

        get_resource_response_200 = cls(
            path=path,
            resource_type=resource_type,
            is_oauth=is_oauth,
            workspace_id=workspace_id,
            description=description,
            value=value,
            extra_perms=extra_perms,
            created_by=created_by,
            edited_at=edited_at,
        )

        get_resource_response_200.additional_properties = d
        return get_resource_response_200

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
