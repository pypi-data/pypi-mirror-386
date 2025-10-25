from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ListStoredFilesResponse200WindmillLargeFilesItem")


@_attrs_define
class ListStoredFilesResponse200WindmillLargeFilesItem:
    """
    Attributes:
        s3 (str):
    """

    s3: str
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        s3 = self.s3

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "s3": s3,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        s3 = d.pop("s3")

        list_stored_files_response_200_windmill_large_files_item = cls(
            s3=s3,
        )

        list_stored_files_response_200_windmill_large_files_item.additional_properties = d
        return list_stored_files_response_200_windmill_large_files_item

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
