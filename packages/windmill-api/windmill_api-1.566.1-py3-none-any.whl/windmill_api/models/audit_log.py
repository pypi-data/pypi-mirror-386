import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.audit_log_action_kind import AuditLogActionKind
from ..models.audit_log_operation import AuditLogOperation
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.audit_log_parameters import AuditLogParameters


T = TypeVar("T", bound="AuditLog")


@_attrs_define
class AuditLog:
    """
    Attributes:
        workspace_id (str):
        id (int):
        timestamp (datetime.datetime):
        username (str):
        operation (AuditLogOperation):
        action_kind (AuditLogActionKind):
        resource (Union[Unset, str]):
        parameters (Union[Unset, AuditLogParameters]):
        span (Union[Unset, str]):
    """

    workspace_id: str
    id: int
    timestamp: datetime.datetime
    username: str
    operation: AuditLogOperation
    action_kind: AuditLogActionKind
    resource: Union[Unset, str] = UNSET
    parameters: Union[Unset, "AuditLogParameters"] = UNSET
    span: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        workspace_id = self.workspace_id
        id = self.id
        timestamp = self.timestamp.isoformat()

        username = self.username
        operation = self.operation.value

        action_kind = self.action_kind.value

        resource = self.resource
        parameters: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.parameters, Unset):
            parameters = self.parameters.to_dict()

        span = self.span

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "workspace_id": workspace_id,
                "id": id,
                "timestamp": timestamp,
                "username": username,
                "operation": operation,
                "action_kind": action_kind,
            }
        )
        if resource is not UNSET:
            field_dict["resource"] = resource
        if parameters is not UNSET:
            field_dict["parameters"] = parameters
        if span is not UNSET:
            field_dict["span"] = span

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.audit_log_parameters import AuditLogParameters

        d = src_dict.copy()
        workspace_id = d.pop("workspace_id")

        id = d.pop("id")

        timestamp = isoparse(d.pop("timestamp"))

        username = d.pop("username")

        operation = AuditLogOperation(d.pop("operation"))

        action_kind = AuditLogActionKind(d.pop("action_kind"))

        resource = d.pop("resource", UNSET)

        _parameters = d.pop("parameters", UNSET)
        parameters: Union[Unset, AuditLogParameters]
        if isinstance(_parameters, Unset):
            parameters = UNSET
        else:
            parameters = AuditLogParameters.from_dict(_parameters)

        span = d.pop("span", UNSET)

        audit_log = cls(
            workspace_id=workspace_id,
            id=id,
            timestamp=timestamp,
            username=username,
            operation=operation,
            action_kind=action_kind,
            resource=resource,
            parameters=parameters,
            span=span,
        )

        audit_log.additional_properties = d
        return audit_log

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
