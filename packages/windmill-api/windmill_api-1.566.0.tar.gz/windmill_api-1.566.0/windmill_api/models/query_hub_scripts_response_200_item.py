from typing import Any, Dict, List, Type, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.query_hub_scripts_response_200_item_kind import QueryHubScriptsResponse200ItemKind

T = TypeVar("T", bound="QueryHubScriptsResponse200Item")


@_attrs_define
class QueryHubScriptsResponse200Item:
    """
    Attributes:
        ask_id (float):
        id (float):
        version_id (float):
        summary (str):
        app (str):
        kind (QueryHubScriptsResponse200ItemKind):
        score (float):
    """

    ask_id: float
    id: float
    version_id: float
    summary: str
    app: str
    kind: QueryHubScriptsResponse200ItemKind
    score: float
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        ask_id = self.ask_id
        id = self.id
        version_id = self.version_id
        summary = self.summary
        app = self.app
        kind = self.kind.value

        score = self.score

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ask_id": ask_id,
                "id": id,
                "version_id": version_id,
                "summary": summary,
                "app": app,
                "kind": kind,
                "score": score,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        ask_id = d.pop("ask_id")

        id = d.pop("id")

        version_id = d.pop("version_id")

        summary = d.pop("summary")

        app = d.pop("app")

        kind = QueryHubScriptsResponse200ItemKind(d.pop("kind"))

        score = d.pop("score")

        query_hub_scripts_response_200_item = cls(
            ask_id=ask_id,
            id=id,
            version_id=version_id,
            summary=summary,
            app=app,
            kind=kind,
            score=score,
        )

        query_hub_scripts_response_200_item.additional_properties = d
        return query_hub_scripts_response_200_item

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
