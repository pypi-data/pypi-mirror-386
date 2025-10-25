from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_config_response_200_alerts_item import GetConfigResponse200AlertsItem


T = TypeVar("T", bound="GetConfigResponse200")


@_attrs_define
class GetConfigResponse200:
    """
    Attributes:
        alerts (Union[Unset, List['GetConfigResponse200AlertsItem']]):
    """

    alerts: Union[Unset, List["GetConfigResponse200AlertsItem"]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        alerts: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.alerts, Unset):
            alerts = []
            for alerts_item_data in self.alerts:
                alerts_item = alerts_item_data.to_dict()

                alerts.append(alerts_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alerts is not UNSET:
            field_dict["alerts"] = alerts

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_config_response_200_alerts_item import GetConfigResponse200AlertsItem

        d = src_dict.copy()
        alerts = []
        _alerts = d.pop("alerts", UNSET)
        for alerts_item_data in _alerts or []:
            alerts_item = GetConfigResponse200AlertsItem.from_dict(alerts_item_data)

            alerts.append(alerts_item)

        get_config_response_200 = cls(
            alerts=alerts,
        )

        get_config_response_200.additional_properties = d
        return get_config_response_200

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
