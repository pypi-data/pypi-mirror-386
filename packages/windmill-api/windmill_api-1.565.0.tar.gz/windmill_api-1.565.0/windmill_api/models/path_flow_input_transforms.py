from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.path_flow_input_transforms_additional_property_type_0 import (
        PathFlowInputTransformsAdditionalPropertyType0,
    )
    from ..models.path_flow_input_transforms_additional_property_type_1 import (
        PathFlowInputTransformsAdditionalPropertyType1,
    )


T = TypeVar("T", bound="PathFlowInputTransforms")


@_attrs_define
class PathFlowInputTransforms:
    """ """

    additional_properties: Dict[
        str, Union["PathFlowInputTransformsAdditionalPropertyType0", "PathFlowInputTransformsAdditionalPropertyType1"]
    ] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.path_flow_input_transforms_additional_property_type_0 import (
            PathFlowInputTransformsAdditionalPropertyType0,
        )

        field_dict: Dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            if isinstance(prop, PathFlowInputTransformsAdditionalPropertyType0):
                field_dict[prop_name] = prop.to_dict()

            else:
                field_dict[prop_name] = prop.to_dict()

        field_dict.update({})

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.path_flow_input_transforms_additional_property_type_0 import (
            PathFlowInputTransformsAdditionalPropertyType0,
        )
        from ..models.path_flow_input_transforms_additional_property_type_1 import (
            PathFlowInputTransformsAdditionalPropertyType1,
        )

        d = src_dict.copy()
        path_flow_input_transforms = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():

            def _parse_additional_property(
                data: object,
            ) -> Union[
                "PathFlowInputTransformsAdditionalPropertyType0", "PathFlowInputTransformsAdditionalPropertyType1"
            ]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    additional_property_type_0 = PathFlowInputTransformsAdditionalPropertyType0.from_dict(data)

                    return additional_property_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                additional_property_type_1 = PathFlowInputTransformsAdditionalPropertyType1.from_dict(data)

                return additional_property_type_1

            additional_property = _parse_additional_property(prop_dict)

            additional_properties[prop_name] = additional_property

        path_flow_input_transforms.additional_properties = additional_properties
        return path_flow_input_transforms

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(
        self, key: str
    ) -> Union["PathFlowInputTransformsAdditionalPropertyType0", "PathFlowInputTransformsAdditionalPropertyType1"]:
        return self.additional_properties[key]

    def __setitem__(
        self,
        key: str,
        value: Union[
            "PathFlowInputTransformsAdditionalPropertyType0", "PathFlowInputTransformsAdditionalPropertyType1"
        ],
    ) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
