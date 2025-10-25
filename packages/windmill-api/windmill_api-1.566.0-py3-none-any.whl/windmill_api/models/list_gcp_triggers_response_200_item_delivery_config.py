from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ListGcpTriggersResponse200ItemDeliveryConfig")


@_attrs_define
class ListGcpTriggersResponse200ItemDeliveryConfig:
    """
    Attributes:
        authenticate (bool):
        audience (Union[Unset, str]):
    """

    authenticate: bool
    audience: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        authenticate = self.authenticate
        audience = self.audience

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "authenticate": authenticate,
            }
        )
        if audience is not UNSET:
            field_dict["audience"] = audience

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        authenticate = d.pop("authenticate")

        audience = d.pop("audience", UNSET)

        list_gcp_triggers_response_200_item_delivery_config = cls(
            authenticate=authenticate,
            audience=audience,
        )

        list_gcp_triggers_response_200_item_delivery_config.additional_properties = d
        return list_gcp_triggers_response_200_item_delivery_config

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
