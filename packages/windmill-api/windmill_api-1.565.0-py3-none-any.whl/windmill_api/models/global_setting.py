from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.global_setting_value import GlobalSettingValue


T = TypeVar("T", bound="GlobalSetting")


@_attrs_define
class GlobalSetting:
    """
    Attributes:
        name (str):
        value (GlobalSettingValue):
    """

    name: str
    value: "GlobalSettingValue"
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        value = self.value.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.global_setting_value import GlobalSettingValue

        d = src_dict.copy()
        name = d.pop("name")

        value = GlobalSettingValue.from_dict(d.pop("value"))

        global_setting = cls(
            name=name,
            value=value,
        )

        global_setting.additional_properties = d
        return global_setting

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
