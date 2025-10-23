from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mqtt_subscribe_topic_qos import MqttSubscribeTopicQos

T = TypeVar("T", bound="MqttSubscribeTopic")


@_attrs_define
class MqttSubscribeTopic:
    """
    Attributes:
        qos (MqttSubscribeTopicQos):
        topic (str):
    """

    qos: MqttSubscribeTopicQos
    topic: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        qos = self.qos.value

        topic = self.topic

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "qos": qos,
                "topic": topic,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        qos = MqttSubscribeTopicQos(d.pop("qos"))

        topic = d.pop("topic")

        mqtt_subscribe_topic = cls(
            qos=qos,
            topic=topic,
        )

        mqtt_subscribe_topic.additional_properties = d
        return mqtt_subscribe_topic

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
