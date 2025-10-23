import datetime
from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="TimeseriesMetricValuesItem")


@_attrs_define
class TimeseriesMetricValuesItem:
    """
    Attributes:
        timestamp (datetime.datetime):
        value (float):
    """

    timestamp: datetime.datetime
    value: float
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        timestamp = self.timestamp.isoformat()

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "timestamp": timestamp,
                "value": value,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        timestamp = isoparse(d.pop("timestamp"))

        value = d.pop("value")

        timeseries_metric_values_item = cls(
            timestamp=timestamp,
            value=value,
        )

        timeseries_metric_values_item.additional_properties = d
        return timeseries_metric_values_item

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
