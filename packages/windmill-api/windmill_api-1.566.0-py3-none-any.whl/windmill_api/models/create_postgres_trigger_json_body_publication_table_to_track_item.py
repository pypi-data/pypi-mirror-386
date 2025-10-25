from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.create_postgres_trigger_json_body_publication_table_to_track_item_table_to_track_item import (
        CreatePostgresTriggerJsonBodyPublicationTableToTrackItemTableToTrackItem,
    )


T = TypeVar("T", bound="CreatePostgresTriggerJsonBodyPublicationTableToTrackItem")


@_attrs_define
class CreatePostgresTriggerJsonBodyPublicationTableToTrackItem:
    """
    Attributes:
        schema_name (str):
        table_to_track (List['CreatePostgresTriggerJsonBodyPublicationTableToTrackItemTableToTrackItem']):
    """

    schema_name: str
    table_to_track: List["CreatePostgresTriggerJsonBodyPublicationTableToTrackItemTableToTrackItem"]
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        schema_name = self.schema_name
        table_to_track = []
        for table_to_track_item_data in self.table_to_track:
            table_to_track_item = table_to_track_item_data.to_dict()

            table_to_track.append(table_to_track_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "schema_name": schema_name,
                "table_to_track": table_to_track,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.create_postgres_trigger_json_body_publication_table_to_track_item_table_to_track_item import (
            CreatePostgresTriggerJsonBodyPublicationTableToTrackItemTableToTrackItem,
        )

        d = src_dict.copy()
        schema_name = d.pop("schema_name")

        table_to_track = []
        _table_to_track = d.pop("table_to_track")
        for table_to_track_item_data in _table_to_track:
            table_to_track_item = CreatePostgresTriggerJsonBodyPublicationTableToTrackItemTableToTrackItem.from_dict(
                table_to_track_item_data
            )

            table_to_track.append(table_to_track_item)

        create_postgres_trigger_json_body_publication_table_to_track_item = cls(
            schema_name=schema_name,
            table_to_track=table_to_track,
        )

        create_postgres_trigger_json_body_publication_table_to_track_item.additional_properties = d
        return create_postgres_trigger_json_body_publication_table_to_track_item

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
