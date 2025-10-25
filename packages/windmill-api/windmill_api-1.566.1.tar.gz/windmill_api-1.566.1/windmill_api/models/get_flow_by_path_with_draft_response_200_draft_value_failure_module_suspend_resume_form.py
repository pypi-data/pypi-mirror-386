from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_flow_by_path_with_draft_response_200_draft_value_failure_module_suspend_resume_form_schema import (
        GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema,
    )


T = TypeVar("T", bound="GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeForm")


@_attrs_define
class GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeForm:
    """
    Attributes:
        schema (Union[Unset, GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema]):
    """

    schema: Union[Unset, "GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        schema: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.schema, Unset):
            schema = self.schema.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if schema is not UNSET:
            field_dict["schema"] = schema

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_flow_by_path_with_draft_response_200_draft_value_failure_module_suspend_resume_form_schema import (
            GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema,
        )

        d = src_dict.copy()
        _schema = d.pop("schema", UNSET)
        schema: Union[Unset, GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema]
        if isinstance(_schema, Unset):
            schema = UNSET
        else:
            schema = GetFlowByPathWithDraftResponse200DraftValueFailureModuleSuspendResumeFormSchema.from_dict(_schema)

        get_flow_by_path_with_draft_response_200_draft_value_failure_module_suspend_resume_form = cls(
            schema=schema,
        )

        get_flow_by_path_with_draft_response_200_draft_value_failure_module_suspend_resume_form.additional_properties = (
            d
        )
        return get_flow_by_path_with_draft_response_200_draft_value_failure_module_suspend_resume_form

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
