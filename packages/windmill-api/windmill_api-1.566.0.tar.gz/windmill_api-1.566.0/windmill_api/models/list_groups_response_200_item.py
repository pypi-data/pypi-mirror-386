from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.list_groups_response_200_item_extra_perms import ListGroupsResponse200ItemExtraPerms


T = TypeVar("T", bound="ListGroupsResponse200Item")


@_attrs_define
class ListGroupsResponse200Item:
    """
    Attributes:
        name (str):
        summary (Union[Unset, str]):
        members (Union[Unset, List[str]]):
        extra_perms (Union[Unset, ListGroupsResponse200ItemExtraPerms]):
    """

    name: str
    summary: Union[Unset, str] = UNSET
    members: Union[Unset, List[str]] = UNSET
    extra_perms: Union[Unset, "ListGroupsResponse200ItemExtraPerms"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        name = self.name
        summary = self.summary
        members: Union[Unset, List[str]] = UNSET
        if not isinstance(self.members, Unset):
            members = self.members

        extra_perms: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.extra_perms, Unset):
            extra_perms = self.extra_perms.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if summary is not UNSET:
            field_dict["summary"] = summary
        if members is not UNSET:
            field_dict["members"] = members
        if extra_perms is not UNSET:
            field_dict["extra_perms"] = extra_perms

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.list_groups_response_200_item_extra_perms import ListGroupsResponse200ItemExtraPerms

        d = src_dict.copy()
        name = d.pop("name")

        summary = d.pop("summary", UNSET)

        members = cast(List[str], d.pop("members", UNSET))

        _extra_perms = d.pop("extra_perms", UNSET)
        extra_perms: Union[Unset, ListGroupsResponse200ItemExtraPerms]
        if isinstance(_extra_perms, Unset):
            extra_perms = UNSET
        else:
            extra_perms = ListGroupsResponse200ItemExtraPerms.from_dict(_extra_perms)

        list_groups_response_200_item = cls(
            name=name,
            summary=summary,
            members=members,
            extra_perms=extra_perms,
        )

        list_groups_response_200_item.additional_properties = d
        return list_groups_response_200_item

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
