from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateResourceJsonBody")


@_attrs_define
class CreateResourceJsonBody:
    """
    Attributes:
        path (str): The path to the resource
        value (Any):
        resource_type (str): The resource_type associated with the resource
        description (Union[Unset, str]): The description of the resource
    """

    path: str
    value: Any
    resource_type: str
    description: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        value = self.value
        resource_type = self.resource_type
        description = self.description

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "value": value,
                "resource_type": resource_type,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        path = d.pop("path")

        value = d.pop("value")

        resource_type = d.pop("resource_type")

        description = d.pop("description", UNSET)

        create_resource_json_body = cls(
            path=path,
            value=value,
            resource_type=resource_type,
            description=description,
        )

        create_resource_json_body.additional_properties = d
        return create_resource_json_body

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
