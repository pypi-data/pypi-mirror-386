from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_git_sync_settings_repositories_item import WorkspaceGitSyncSettingsRepositoriesItem


T = TypeVar("T", bound="WorkspaceGitSyncSettings")


@_attrs_define
class WorkspaceGitSyncSettings:
    """
    Attributes:
        repositories (Union[Unset, List['WorkspaceGitSyncSettingsRepositoriesItem']]):
    """

    repositories: Union[Unset, List["WorkspaceGitSyncSettingsRepositoriesItem"]] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        repositories: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.repositories, Unset):
            repositories = []
            for repositories_item_data in self.repositories:
                repositories_item = repositories_item_data.to_dict()

                repositories.append(repositories_item)

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if repositories is not UNSET:
            field_dict["repositories"] = repositories

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.workspace_git_sync_settings_repositories_item import WorkspaceGitSyncSettingsRepositoriesItem

        d = src_dict.copy()
        repositories = []
        _repositories = d.pop("repositories", UNSET)
        for repositories_item_data in _repositories or []:
            repositories_item = WorkspaceGitSyncSettingsRepositoriesItem.from_dict(repositories_item_data)

            repositories.append(repositories_item)

        workspace_git_sync_settings = cls(
            repositories=repositories,
        )

        workspace_git_sync_settings.additional_properties = d
        return workspace_git_sync_settings

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
