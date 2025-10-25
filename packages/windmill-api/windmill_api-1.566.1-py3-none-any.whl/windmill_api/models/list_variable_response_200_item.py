import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.list_variable_response_200_item_extra_perms import ListVariableResponse200ItemExtraPerms


T = TypeVar("T", bound="ListVariableResponse200Item")


@_attrs_define
class ListVariableResponse200Item:
    """
    Attributes:
        workspace_id (str):
        path (str):
        is_secret (bool):
        extra_perms (ListVariableResponse200ItemExtraPerms):
        value (Union[Unset, str]):
        description (Union[Unset, str]):
        account (Union[Unset, int]):
        is_oauth (Union[Unset, bool]):
        is_expired (Union[Unset, bool]):
        refresh_error (Union[Unset, str]):
        is_linked (Union[Unset, bool]):
        is_refreshed (Union[Unset, bool]):
        expires_at (Union[Unset, datetime.datetime]):
    """

    workspace_id: str
    path: str
    is_secret: bool
    extra_perms: "ListVariableResponse200ItemExtraPerms"
    value: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    account: Union[Unset, int] = UNSET
    is_oauth: Union[Unset, bool] = UNSET
    is_expired: Union[Unset, bool] = UNSET
    refresh_error: Union[Unset, str] = UNSET
    is_linked: Union[Unset, bool] = UNSET
    is_refreshed: Union[Unset, bool] = UNSET
    expires_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        workspace_id = self.workspace_id
        path = self.path
        is_secret = self.is_secret
        extra_perms = self.extra_perms.to_dict()

        value = self.value
        description = self.description
        account = self.account
        is_oauth = self.is_oauth
        is_expired = self.is_expired
        refresh_error = self.refresh_error
        is_linked = self.is_linked
        is_refreshed = self.is_refreshed
        expires_at: Union[Unset, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "path": path,
                "is_secret": is_secret,
                "extra_perms": extra_perms,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value
        if description is not UNSET:
            field_dict["description"] = description
        if account is not UNSET:
            field_dict["account"] = account
        if is_oauth is not UNSET:
            field_dict["is_oauth"] = is_oauth
        if is_expired is not UNSET:
            field_dict["is_expired"] = is_expired
        if refresh_error is not UNSET:
            field_dict["refresh_error"] = refresh_error
        if is_linked is not UNSET:
            field_dict["is_linked"] = is_linked
        if is_refreshed is not UNSET:
            field_dict["is_refreshed"] = is_refreshed
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.list_variable_response_200_item_extra_perms import ListVariableResponse200ItemExtraPerms

        d = src_dict.copy()
        workspace_id = d.pop("workspace_id")

        path = d.pop("path")

        is_secret = d.pop("is_secret")

        extra_perms = ListVariableResponse200ItemExtraPerms.from_dict(d.pop("extra_perms"))

        value = d.pop("value", UNSET)

        description = d.pop("description", UNSET)

        account = d.pop("account", UNSET)

        is_oauth = d.pop("is_oauth", UNSET)

        is_expired = d.pop("is_expired", UNSET)

        refresh_error = d.pop("refresh_error", UNSET)

        is_linked = d.pop("is_linked", UNSET)

        is_refreshed = d.pop("is_refreshed", UNSET)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: Union[Unset, datetime.datetime]
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        list_variable_response_200_item = cls(
            workspace_id=workspace_id,
            path=path,
            is_secret=is_secret,
            extra_perms=extra_perms,
            value=value,
            description=description,
            account=account,
            is_oauth=is_oauth,
            is_expired=is_expired,
            refresh_error=refresh_error,
            is_linked=is_linked,
            is_refreshed=is_refreshed,
            expires_at=expires_at,
        )

        list_variable_response_200_item.additional_properties = d
        return list_variable_response_200_item

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
