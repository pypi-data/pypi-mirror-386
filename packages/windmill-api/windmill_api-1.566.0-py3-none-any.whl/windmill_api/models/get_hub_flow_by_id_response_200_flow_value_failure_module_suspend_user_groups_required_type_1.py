from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_hub_flow_by_id_response_200_flow_value_failure_module_suspend_user_groups_required_type_1_type import (
    GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1Type,
)

T = TypeVar("T", bound="GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1")


@_attrs_define
class GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1:
    """
    Attributes:
        expr (str):
        type (GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1Type):
    """

    expr: str
    type: GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1Type
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        expr = self.expr
        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "expr": expr,
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        expr = d.pop("expr")

        type = GetHubFlowByIdResponse200FlowValueFailureModuleSuspendUserGroupsRequiredType1Type(d.pop("type"))

        get_hub_flow_by_id_response_200_flow_value_failure_module_suspend_user_groups_required_type_1 = cls(
            expr=expr,
            type=type,
        )

        get_hub_flow_by_id_response_200_flow_value_failure_module_suspend_user_groups_required_type_1.additional_properties = (
            d
        )
        return get_hub_flow_by_id_response_200_flow_value_failure_module_suspend_user_groups_required_type_1

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
