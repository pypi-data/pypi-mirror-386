from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CompletedJobFlowStatusFailureModuleBranchall")


@_attrs_define
class CompletedJobFlowStatusFailureModuleBranchall:
    """
    Attributes:
        branch (int):
        len_ (int):
    """

    branch: int
    len_: int
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        branch = self.branch
        len_ = self.len_

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "branch": branch,
                "len": len_,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        branch = d.pop("branch")

        len_ = d.pop("len")

        completed_job_flow_status_failure_module_branchall = cls(
            branch=branch,
            len_=len_,
        )

        completed_job_flow_status_failure_module_branchall.additional_properties = d
        return completed_job_flow_status_failure_module_branchall

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
