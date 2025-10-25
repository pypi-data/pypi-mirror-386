from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_draft_json_body_typ import CreateDraftJsonBodyTyp
from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDraftJsonBody")


@_attrs_define
class CreateDraftJsonBody:
    """
    Attributes:
        path (str):
        typ (CreateDraftJsonBodyTyp):
        value (Union[Unset, Any]):
    """

    path: str
    typ: CreateDraftJsonBodyTyp
    value: Union[Unset, Any] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        typ = self.typ.value

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "typ": typ,
            }
        )
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        path = d.pop("path")

        typ = CreateDraftJsonBodyTyp(d.pop("typ"))

        value = d.pop("value", UNSET)

        create_draft_json_body = cls(
            path=path,
            typ=typ,
            value=value,
        )

        create_draft_json_body.additional_properties = d
        return create_draft_json_body

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
