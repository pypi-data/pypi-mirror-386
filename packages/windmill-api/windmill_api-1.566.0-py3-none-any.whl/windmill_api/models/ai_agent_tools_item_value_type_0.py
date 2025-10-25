from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.ai_agent_tools_item_value_type_0_tool_type import AiAgentToolsItemValueType0ToolType

T = TypeVar("T", bound="AiAgentToolsItemValueType0")


@_attrs_define
class AiAgentToolsItemValueType0:
    """
    Attributes:
        tool_type (AiAgentToolsItemValueType0ToolType):
    """

    tool_type: AiAgentToolsItemValueType0ToolType
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        tool_type = self.tool_type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tool_type": tool_type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        tool_type = AiAgentToolsItemValueType0ToolType(d.pop("tool_type"))

        ai_agent_tools_item_value_type_0 = cls(
            tool_type=tool_type,
        )

        ai_agent_tools_item_value_type_0.additional_properties = d
        return ai_agent_tools_item_value_type_0

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
