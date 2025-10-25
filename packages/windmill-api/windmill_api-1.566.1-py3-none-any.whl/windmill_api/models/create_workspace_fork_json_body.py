from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateWorkspaceForkJsonBody")


@_attrs_define
class CreateWorkspaceForkJsonBody:
    """
    Attributes:
        id (str):
        name (str):
        parent_workspace_id (str):
        username (Union[Unset, str]):
        color (Union[Unset, str]):
    """

    id: str
    name: str
    parent_workspace_id: str
    username: Union[Unset, str] = UNSET
    color: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        name = self.name
        parent_workspace_id = self.parent_workspace_id
        username = self.username
        color = self.color

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "parent_workspace_id": parent_workspace_id,
            }
        )
        if username is not UNSET:
            field_dict["username"] = username
        if color is not UNSET:
            field_dict["color"] = color

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id")

        name = d.pop("name")

        parent_workspace_id = d.pop("parent_workspace_id")

        username = d.pop("username", UNSET)

        color = d.pop("color", UNSET)

        create_workspace_fork_json_body = cls(
            id=id,
            name=name,
            parent_workspace_id=parent_workspace_id,
            username=username,
            color=color,
        )

        create_workspace_fork_json_body.additional_properties = d
        return create_workspace_fork_json_body

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
