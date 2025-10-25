import datetime
from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateVariableJsonBody")


@_attrs_define
class CreateVariableJsonBody:
    """
    Attributes:
        path (str): The path to the variable
        value (str): The value of the variable
        is_secret (bool): Whether the variable is a secret
        description (str): The description of the variable
        account (Union[Unset, int]): The account identifier
        is_oauth (Union[Unset, bool]): Whether the variable is an OAuth variable
        expires_at (Union[Unset, datetime.datetime]): The expiration date of the variable
    """

    path: str
    value: str
    is_secret: bool
    description: str
    account: Union[Unset, int] = UNSET
    is_oauth: Union[Unset, bool] = UNSET
    expires_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        value = self.value
        is_secret = self.is_secret
        description = self.description
        account = self.account
        is_oauth = self.is_oauth
        expires_at: Union[Unset, str] = UNSET
        if not isinstance(self.expires_at, Unset):
            expires_at = self.expires_at.isoformat()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "value": value,
                "is_secret": is_secret,
                "description": description,
            }
        )
        if account is not UNSET:
            field_dict["account"] = account
        if is_oauth is not UNSET:
            field_dict["is_oauth"] = is_oauth
        if expires_at is not UNSET:
            field_dict["expires_at"] = expires_at

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        path = d.pop("path")

        value = d.pop("value")

        is_secret = d.pop("is_secret")

        description = d.pop("description")

        account = d.pop("account", UNSET)

        is_oauth = d.pop("is_oauth", UNSET)

        _expires_at = d.pop("expires_at", UNSET)
        expires_at: Union[Unset, datetime.datetime]
        if isinstance(_expires_at, Unset):
            expires_at = UNSET
        else:
            expires_at = isoparse(_expires_at)

        create_variable_json_body = cls(
            path=path,
            value=value,
            is_secret=is_secret,
            description=description,
            account=account,
            is_oauth=is_oauth,
            expires_at=expires_at,
        )

        create_variable_json_body.additional_properties = d
        return create_variable_json_body

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
