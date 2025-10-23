from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_script_json_body_assets_item_access_type import CreateScriptJsonBodyAssetsItemAccessType
from ..models.create_script_json_body_assets_item_alt_access_type import CreateScriptJsonBodyAssetsItemAltAccessType
from ..models.create_script_json_body_assets_item_kind import CreateScriptJsonBodyAssetsItemKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateScriptJsonBodyAssetsItem")


@_attrs_define
class CreateScriptJsonBodyAssetsItem:
    """
    Attributes:
        path (str):
        kind (CreateScriptJsonBodyAssetsItemKind):
        access_type (Union[Unset, CreateScriptJsonBodyAssetsItemAccessType]):
        alt_access_type (Union[Unset, CreateScriptJsonBodyAssetsItemAltAccessType]):
    """

    path: str
    kind: CreateScriptJsonBodyAssetsItemKind
    access_type: Union[Unset, CreateScriptJsonBodyAssetsItemAccessType] = UNSET
    alt_access_type: Union[Unset, CreateScriptJsonBodyAssetsItemAltAccessType] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        kind = self.kind.value

        access_type: Union[Unset, str] = UNSET
        if not isinstance(self.access_type, Unset):
            access_type = self.access_type.value

        alt_access_type: Union[Unset, str] = UNSET
        if not isinstance(self.alt_access_type, Unset):
            alt_access_type = self.alt_access_type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "kind": kind,
            }
        )
        if access_type is not UNSET:
            field_dict["access_type"] = access_type
        if alt_access_type is not UNSET:
            field_dict["alt_access_type"] = alt_access_type

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        path = d.pop("path")

        kind = CreateScriptJsonBodyAssetsItemKind(d.pop("kind"))

        _access_type = d.pop("access_type", UNSET)
        access_type: Union[Unset, CreateScriptJsonBodyAssetsItemAccessType]
        if isinstance(_access_type, Unset):
            access_type = UNSET
        else:
            access_type = CreateScriptJsonBodyAssetsItemAccessType(_access_type)

        _alt_access_type = d.pop("alt_access_type", UNSET)
        alt_access_type: Union[Unset, CreateScriptJsonBodyAssetsItemAltAccessType]
        if isinstance(_alt_access_type, Unset):
            alt_access_type = UNSET
        else:
            alt_access_type = CreateScriptJsonBodyAssetsItemAltAccessType(_alt_access_type)

        create_script_json_body_assets_item = cls(
            path=path,
            kind=kind,
            access_type=access_type,
            alt_access_type=alt_access_type,
        )

        create_script_json_body_assets_item.additional_properties = d
        return create_script_json_body_assets_item

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
