from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.path_flow_type import PathFlowType

if TYPE_CHECKING:
    from ..models.path_flow_input_transforms import PathFlowInputTransforms


T = TypeVar("T", bound="PathFlow")


@_attrs_define
class PathFlow:
    """
    Attributes:
        input_transforms (PathFlowInputTransforms):
        path (str):
        type (PathFlowType):
    """

    input_transforms: "PathFlowInputTransforms"
    path: str
    type: PathFlowType
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        input_transforms = self.input_transforms.to_dict()

        path = self.path
        type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "input_transforms": input_transforms,
                "path": path,
                "type": type,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.path_flow_input_transforms import PathFlowInputTransforms

        d = src_dict.copy()
        input_transforms = PathFlowInputTransforms.from_dict(d.pop("input_transforms"))

        path = d.pop("path")

        type = PathFlowType(d.pop("type"))

        path_flow = cls(
            input_transforms=input_transforms,
            path=path,
            type=type,
        )

        path_flow.additional_properties = d
        return path_flow

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
