from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UpdateUserJsonBody")


@_attrs_define
class UpdateUserJsonBody:
    """
    Attributes:
        is_admin (Union[Unset, bool]):
        operator (Union[Unset, bool]):
        disabled (Union[Unset, bool]):
    """

    is_admin: Union[Unset, bool] = UNSET
    operator: Union[Unset, bool] = UNSET
    disabled: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        is_admin = self.is_admin
        operator = self.operator
        disabled = self.disabled

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if is_admin is not UNSET:
            field_dict["is_admin"] = is_admin
        if operator is not UNSET:
            field_dict["operator"] = operator
        if disabled is not UNSET:
            field_dict["disabled"] = disabled

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        is_admin = d.pop("is_admin", UNSET)

        operator = d.pop("operator", UNSET)

        disabled = d.pop("disabled", UNSET)

        update_user_json_body = cls(
            is_admin=is_admin,
            operator=operator,
            disabled=disabled,
        )

        update_user_json_body.additional_properties = d
        return update_user_json_body

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
