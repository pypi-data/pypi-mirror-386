from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.new_script_with_draft_draft_assets_item_access_type import NewScriptWithDraftDraftAssetsItemAccessType
from ..models.new_script_with_draft_draft_assets_item_alt_access_type import (
    NewScriptWithDraftDraftAssetsItemAltAccessType,
)
from ..models.new_script_with_draft_draft_assets_item_kind import NewScriptWithDraftDraftAssetsItemKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="NewScriptWithDraftDraftAssetsItem")


@_attrs_define
class NewScriptWithDraftDraftAssetsItem:
    """
    Attributes:
        path (str):
        kind (NewScriptWithDraftDraftAssetsItemKind):
        access_type (Union[Unset, NewScriptWithDraftDraftAssetsItemAccessType]):
        alt_access_type (Union[Unset, NewScriptWithDraftDraftAssetsItemAltAccessType]):
    """

    path: str
    kind: NewScriptWithDraftDraftAssetsItemKind
    access_type: Union[Unset, NewScriptWithDraftDraftAssetsItemAccessType] = UNSET
    alt_access_type: Union[Unset, NewScriptWithDraftDraftAssetsItemAltAccessType] = UNSET
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

        kind = NewScriptWithDraftDraftAssetsItemKind(d.pop("kind"))

        _access_type = d.pop("access_type", UNSET)
        access_type: Union[Unset, NewScriptWithDraftDraftAssetsItemAccessType]
        if isinstance(_access_type, Unset):
            access_type = UNSET
        else:
            access_type = NewScriptWithDraftDraftAssetsItemAccessType(_access_type)

        _alt_access_type = d.pop("alt_access_type", UNSET)
        alt_access_type: Union[Unset, NewScriptWithDraftDraftAssetsItemAltAccessType]
        if isinstance(_alt_access_type, Unset):
            alt_access_type = UNSET
        else:
            alt_access_type = NewScriptWithDraftDraftAssetsItemAltAccessType(_alt_access_type)

        new_script_with_draft_draft_assets_item = cls(
            path=path,
            kind=kind,
            access_type=access_type,
            alt_access_type=alt_access_type,
        )

        new_script_with_draft_draft_assets_item.additional_properties = d
        return new_script_with_draft_draft_assets_item

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
