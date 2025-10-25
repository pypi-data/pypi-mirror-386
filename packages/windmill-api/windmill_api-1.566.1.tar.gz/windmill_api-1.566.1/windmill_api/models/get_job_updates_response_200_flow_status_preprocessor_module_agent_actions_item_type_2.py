from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_job_updates_response_200_flow_status_preprocessor_module_agent_actions_item_type_2_type import (
    GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2Type,
)

T = TypeVar("T", bound="GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2")


@_attrs_define
class GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2:
    """
    Attributes:
        type (GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2Type):
    """

    type: GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2Type
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        type = GetJobUpdatesResponse200FlowStatusPreprocessorModuleAgentActionsItemType2Type(d.pop("type"))

        get_job_updates_response_200_flow_status_preprocessor_module_agent_actions_item_type_2 = cls(
            type=type,
        )

        get_job_updates_response_200_flow_status_preprocessor_module_agent_actions_item_type_2.additional_properties = d
        return get_job_updates_response_200_flow_status_preprocessor_module_agent_actions_item_type_2

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
