from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.agent_tool_value_type_0 import AgentToolValueType0
    from ..models.agent_tool_value_type_1 import AgentToolValueType1


T = TypeVar("T", bound="AgentTool")


@_attrs_define
class AgentTool:
    """
    Attributes:
        id (str):
        value (Union['AgentToolValueType0', 'AgentToolValueType1']):
        summary (Union[Unset, str]):
    """

    id: str
    value: Union["AgentToolValueType0", "AgentToolValueType1"]
    summary: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.agent_tool_value_type_0 import AgentToolValueType0

        id = self.id
        value: Dict[str, Any]

        if isinstance(self.value, AgentToolValueType0):
            value = self.value.to_dict()

        else:
            value = self.value.to_dict()

        summary = self.summary

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "value": value,
            }
        )
        if summary is not UNSET:
            field_dict["summary"] = summary

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.agent_tool_value_type_0 import AgentToolValueType0
        from ..models.agent_tool_value_type_1 import AgentToolValueType1

        d = src_dict.copy()
        id = d.pop("id")

        def _parse_value(data: object) -> Union["AgentToolValueType0", "AgentToolValueType1"]:
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                value_type_0 = AgentToolValueType0.from_dict(data)

                return value_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            value_type_1 = AgentToolValueType1.from_dict(data)

            return value_type_1

        value = _parse_value(d.pop("value"))

        summary = d.pop("summary", UNSET)

        agent_tool = cls(
            id=id,
            value=value,
            summary=summary,
        )

        agent_tool.additional_properties = d
        return agent_tool

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
