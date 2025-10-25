from typing import Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.mcp_tool_value_tool_type import McpToolValueToolType
from ..types import UNSET, Unset

T = TypeVar("T", bound="McpToolValue")


@_attrs_define
class McpToolValue:
    """
    Attributes:
        tool_type (McpToolValueToolType):
        resource_path (str):
        include_tools (Union[Unset, List[str]]):
        exclude_tools (Union[Unset, List[str]]):
    """

    tool_type: McpToolValueToolType
    resource_path: str
    include_tools: Union[Unset, List[str]] = UNSET
    exclude_tools: Union[Unset, List[str]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        tool_type = self.tool_type.value

        resource_path = self.resource_path
        include_tools: Union[Unset, List[str]] = UNSET
        if not isinstance(self.include_tools, Unset):
            include_tools = self.include_tools

        exclude_tools: Union[Unset, List[str]] = UNSET
        if not isinstance(self.exclude_tools, Unset):
            exclude_tools = self.exclude_tools

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "tool_type": tool_type,
                "resource_path": resource_path,
            }
        )
        if include_tools is not UNSET:
            field_dict["include_tools"] = include_tools
        if exclude_tools is not UNSET:
            field_dict["exclude_tools"] = exclude_tools

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        tool_type = McpToolValueToolType(d.pop("tool_type"))

        resource_path = d.pop("resource_path")

        include_tools = cast(List[str], d.pop("include_tools", UNSET))

        exclude_tools = cast(List[str], d.pop("exclude_tools", UNSET))

        mcp_tool_value = cls(
            tool_type=tool_type,
            resource_path=resource_path,
            include_tools=include_tools,
            exclude_tools=exclude_tools,
        )

        mcp_tool_value.additional_properties = d
        return mcp_tool_value

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
