from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.get_large_file_storage_config_response_200_secondary_storage_additional_property_type import (
    GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalPropertyType,
)
from ..types import UNSET, Unset

T = TypeVar("T", bound="GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalProperty")


@_attrs_define
class GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalProperty:
    """
    Attributes:
        type (Union[Unset, GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalPropertyType]):
        s3_resource_path (Union[Unset, str]):
        azure_blob_resource_path (Union[Unset, str]):
        gcs_resource_path (Union[Unset, str]):
        public_resource (Union[Unset, bool]):
    """

    type: Union[Unset, GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalPropertyType] = UNSET
    s3_resource_path: Union[Unset, str] = UNSET
    azure_blob_resource_path: Union[Unset, str] = UNSET
    gcs_resource_path: Union[Unset, str] = UNSET
    public_resource: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        s3_resource_path = self.s3_resource_path
        azure_blob_resource_path = self.azure_blob_resource_path
        gcs_resource_path = self.gcs_resource_path
        public_resource = self.public_resource

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type is not UNSET:
            field_dict["type"] = type
        if s3_resource_path is not UNSET:
            field_dict["s3_resource_path"] = s3_resource_path
        if azure_blob_resource_path is not UNSET:
            field_dict["azure_blob_resource_path"] = azure_blob_resource_path
        if gcs_resource_path is not UNSET:
            field_dict["gcs_resource_path"] = gcs_resource_path
        if public_resource is not UNSET:
            field_dict["public_resource"] = public_resource

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        _type = d.pop("type", UNSET)
        type: Union[Unset, GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalPropertyType]
        if isinstance(_type, Unset):
            type = UNSET
        else:
            type = GetLargeFileStorageConfigResponse200SecondaryStorageAdditionalPropertyType(_type)

        s3_resource_path = d.pop("s3_resource_path", UNSET)

        azure_blob_resource_path = d.pop("azure_blob_resource_path", UNSET)

        gcs_resource_path = d.pop("gcs_resource_path", UNSET)

        public_resource = d.pop("public_resource", UNSET)

        get_large_file_storage_config_response_200_secondary_storage_additional_property = cls(
            type=type,
            s3_resource_path=s3_resource_path,
            azure_blob_resource_path=azure_blob_resource_path,
            gcs_resource_path=gcs_resource_path,
            public_resource=public_resource,
        )

        get_large_file_storage_config_response_200_secondary_storage_additional_property.additional_properties = d
        return get_large_file_storage_config_response_200_secondary_storage_additional_property

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
