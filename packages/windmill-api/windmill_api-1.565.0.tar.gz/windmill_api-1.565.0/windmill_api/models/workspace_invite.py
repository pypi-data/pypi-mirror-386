from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceInvite")


@_attrs_define
class WorkspaceInvite:
    """
    Attributes:
        workspace_id (str):
        email (str):
        is_admin (bool):
        operator (bool):
        parent_workspace_id (Union[Unset, None, str]):
    """

    workspace_id: str
    email: str
    is_admin: bool
    operator: bool
    parent_workspace_id: Union[Unset, None, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        workspace_id = self.workspace_id
        email = self.email
        is_admin = self.is_admin
        operator = self.operator
        parent_workspace_id = self.parent_workspace_id

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "email": email,
                "is_admin": is_admin,
                "operator": operator,
            }
        )
        if parent_workspace_id is not UNSET:
            field_dict["parent_workspace_id"] = parent_workspace_id

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        workspace_id = d.pop("workspace_id")

        email = d.pop("email")

        is_admin = d.pop("is_admin")

        operator = d.pop("operator")

        parent_workspace_id = d.pop("parent_workspace_id", UNSET)

        workspace_invite = cls(
            workspace_id=workspace_id,
            email=email,
            is_admin=is_admin,
            operator=operator,
            parent_workspace_id=parent_workspace_id,
        )

        workspace_invite.additional_properties = d
        return workspace_invite

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
