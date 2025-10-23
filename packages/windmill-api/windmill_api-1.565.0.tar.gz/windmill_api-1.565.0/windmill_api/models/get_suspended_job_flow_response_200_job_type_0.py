import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.get_suspended_job_flow_response_200_job_type_0_job_kind import (
    GetSuspendedJobFlowResponse200JobType0JobKind,
)
from ..models.get_suspended_job_flow_response_200_job_type_0_language import (
    GetSuspendedJobFlowResponse200JobType0Language,
)
from ..models.get_suspended_job_flow_response_200_job_type_0_type import GetSuspendedJobFlowResponse200JobType0Type
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.get_suspended_job_flow_response_200_job_type_0_args import GetSuspendedJobFlowResponse200JobType0Args
    from ..models.get_suspended_job_flow_response_200_job_type_0_flow_status import (
        GetSuspendedJobFlowResponse200JobType0FlowStatus,
    )
    from ..models.get_suspended_job_flow_response_200_job_type_0_raw_flow import (
        GetSuspendedJobFlowResponse200JobType0RawFlow,
    )
    from ..models.get_suspended_job_flow_response_200_job_type_0_workflow_as_code_status import (
        GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus,
    )


T = TypeVar("T", bound="GetSuspendedJobFlowResponse200JobType0")


@_attrs_define
class GetSuspendedJobFlowResponse200JobType0:
    """
    Attributes:
        id (str):
        created_by (str):
        created_at (datetime.datetime):
        started_at (datetime.datetime):
        duration_ms (int):
        success (bool):
        canceled (bool):
        job_kind (GetSuspendedJobFlowResponse200JobType0JobKind):
        permissioned_as (str): The user (u/userfoo) or group (g/groupfoo) whom
            the execution of this script will be permissioned_as and by extension its DT_TOKEN.
        is_flow_step (bool):
        is_skipped (bool):
        email (str):
        visible_to_owner (bool):
        tag (str):
        workspace_id (Union[Unset, str]):
        parent_job (Union[Unset, str]):
        script_path (Union[Unset, str]):
        script_hash (Union[Unset, str]):
        args (Union[Unset, GetSuspendedJobFlowResponse200JobType0Args]): The arguments to pass to the script or flow
        result (Union[Unset, Any]):
        logs (Union[Unset, str]):
        deleted (Union[Unset, bool]):
        raw_code (Union[Unset, str]):
        canceled_by (Union[Unset, str]):
        canceled_reason (Union[Unset, str]):
        schedule_path (Union[Unset, str]):
        flow_status (Union[Unset, GetSuspendedJobFlowResponse200JobType0FlowStatus]):
        workflow_as_code_status (Union[Unset, GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus]):
        raw_flow (Union[Unset, GetSuspendedJobFlowResponse200JobType0RawFlow]):
        language (Union[Unset, GetSuspendedJobFlowResponse200JobType0Language]):
        mem_peak (Union[Unset, int]):
        priority (Union[Unset, int]):
        labels (Union[Unset, List[str]]):
        self_wait_time_ms (Union[Unset, float]):
        aggregate_wait_time_ms (Union[Unset, float]):
        preprocessed (Union[Unset, bool]):
        worker (Union[Unset, str]):
        type (Union[Unset, GetSuspendedJobFlowResponse200JobType0Type]):
    """

    id: str
    created_by: str
    created_at: datetime.datetime
    started_at: datetime.datetime
    duration_ms: int
    success: bool
    canceled: bool
    job_kind: GetSuspendedJobFlowResponse200JobType0JobKind
    permissioned_as: str
    is_flow_step: bool
    is_skipped: bool
    email: str
    visible_to_owner: bool
    tag: str
    workspace_id: Union[Unset, str] = UNSET
    parent_job: Union[Unset, str] = UNSET
    script_path: Union[Unset, str] = UNSET
    script_hash: Union[Unset, str] = UNSET
    args: Union[Unset, "GetSuspendedJobFlowResponse200JobType0Args"] = UNSET
    result: Union[Unset, Any] = UNSET
    logs: Union[Unset, str] = UNSET
    deleted: Union[Unset, bool] = UNSET
    raw_code: Union[Unset, str] = UNSET
    canceled_by: Union[Unset, str] = UNSET
    canceled_reason: Union[Unset, str] = UNSET
    schedule_path: Union[Unset, str] = UNSET
    flow_status: Union[Unset, "GetSuspendedJobFlowResponse200JobType0FlowStatus"] = UNSET
    workflow_as_code_status: Union[Unset, "GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus"] = UNSET
    raw_flow: Union[Unset, "GetSuspendedJobFlowResponse200JobType0RawFlow"] = UNSET
    language: Union[Unset, GetSuspendedJobFlowResponse200JobType0Language] = UNSET
    mem_peak: Union[Unset, int] = UNSET
    priority: Union[Unset, int] = UNSET
    labels: Union[Unset, List[str]] = UNSET
    self_wait_time_ms: Union[Unset, float] = UNSET
    aggregate_wait_time_ms: Union[Unset, float] = UNSET
    preprocessed: Union[Unset, bool] = UNSET
    worker: Union[Unset, str] = UNSET
    type: Union[Unset, GetSuspendedJobFlowResponse200JobType0Type] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id
        created_by = self.created_by
        created_at = self.created_at.isoformat()

        started_at = self.started_at.isoformat()

        duration_ms = self.duration_ms
        success = self.success
        canceled = self.canceled
        job_kind = self.job_kind.value

        permissioned_as = self.permissioned_as
        is_flow_step = self.is_flow_step
        is_skipped = self.is_skipped
        email = self.email
        visible_to_owner = self.visible_to_owner
        tag = self.tag
        workspace_id = self.workspace_id
        parent_job = self.parent_job
        script_path = self.script_path
        script_hash = self.script_hash
        args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.args, Unset):
            args = self.args.to_dict()

        result = self.result
        logs = self.logs
        deleted = self.deleted
        raw_code = self.raw_code
        canceled_by = self.canceled_by
        canceled_reason = self.canceled_reason
        schedule_path = self.schedule_path
        flow_status: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.flow_status, Unset):
            flow_status = self.flow_status.to_dict()

        workflow_as_code_status: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.workflow_as_code_status, Unset):
            workflow_as_code_status = self.workflow_as_code_status.to_dict()

        raw_flow: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.raw_flow, Unset):
            raw_flow = self.raw_flow.to_dict()

        language: Union[Unset, str] = UNSET
        if not isinstance(self.language, Unset):
            language = self.language.value

        mem_peak = self.mem_peak
        priority = self.priority
        labels: Union[Unset, List[str]] = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels

        self_wait_time_ms = self.self_wait_time_ms
        aggregate_wait_time_ms = self.aggregate_wait_time_ms
        preprocessed = self.preprocessed
        worker = self.worker
        type: Union[Unset, str] = UNSET
        if not isinstance(self.type, Unset):
            type = self.type.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "created_by": created_by,
                "created_at": created_at,
                "started_at": started_at,
                "duration_ms": duration_ms,
                "success": success,
                "canceled": canceled,
                "job_kind": job_kind,
                "permissioned_as": permissioned_as,
                "is_flow_step": is_flow_step,
                "is_skipped": is_skipped,
                "email": email,
                "visible_to_owner": visible_to_owner,
                "tag": tag,
            }
        )
        if workspace_id is not UNSET:
            field_dict["workspace_id"] = workspace_id
        if parent_job is not UNSET:
            field_dict["parent_job"] = parent_job
        if script_path is not UNSET:
            field_dict["script_path"] = script_path
        if script_hash is not UNSET:
            field_dict["script_hash"] = script_hash
        if args is not UNSET:
            field_dict["args"] = args
        if result is not UNSET:
            field_dict["result"] = result
        if logs is not UNSET:
            field_dict["logs"] = logs
        if deleted is not UNSET:
            field_dict["deleted"] = deleted
        if raw_code is not UNSET:
            field_dict["raw_code"] = raw_code
        if canceled_by is not UNSET:
            field_dict["canceled_by"] = canceled_by
        if canceled_reason is not UNSET:
            field_dict["canceled_reason"] = canceled_reason
        if schedule_path is not UNSET:
            field_dict["schedule_path"] = schedule_path
        if flow_status is not UNSET:
            field_dict["flow_status"] = flow_status
        if workflow_as_code_status is not UNSET:
            field_dict["workflow_as_code_status"] = workflow_as_code_status
        if raw_flow is not UNSET:
            field_dict["raw_flow"] = raw_flow
        if language is not UNSET:
            field_dict["language"] = language
        if mem_peak is not UNSET:
            field_dict["mem_peak"] = mem_peak
        if priority is not UNSET:
            field_dict["priority"] = priority
        if labels is not UNSET:
            field_dict["labels"] = labels
        if self_wait_time_ms is not UNSET:
            field_dict["self_wait_time_ms"] = self_wait_time_ms
        if aggregate_wait_time_ms is not UNSET:
            field_dict["aggregate_wait_time_ms"] = aggregate_wait_time_ms
        if preprocessed is not UNSET:
            field_dict["preprocessed"] = preprocessed
        if worker is not UNSET:
            field_dict["worker"] = worker
        if type is not UNSET:
            field_dict["type"] = type

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.get_suspended_job_flow_response_200_job_type_0_args import (
            GetSuspendedJobFlowResponse200JobType0Args,
        )
        from ..models.get_suspended_job_flow_response_200_job_type_0_flow_status import (
            GetSuspendedJobFlowResponse200JobType0FlowStatus,
        )
        from ..models.get_suspended_job_flow_response_200_job_type_0_raw_flow import (
            GetSuspendedJobFlowResponse200JobType0RawFlow,
        )
        from ..models.get_suspended_job_flow_response_200_job_type_0_workflow_as_code_status import (
            GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus,
        )

        d = src_dict.copy()
        id = d.pop("id")

        created_by = d.pop("created_by")

        created_at = isoparse(d.pop("created_at"))

        started_at = isoparse(d.pop("started_at"))

        duration_ms = d.pop("duration_ms")

        success = d.pop("success")

        canceled = d.pop("canceled")

        job_kind = GetSuspendedJobFlowResponse200JobType0JobKind(d.pop("job_kind"))

        permissioned_as = d.pop("permissioned_as")

        is_flow_step = d.pop("is_flow_step")

        is_skipped = d.pop("is_skipped")

        email = d.pop("email")

        visible_to_owner = d.pop("visible_to_owner")

        tag = d.pop("tag")

        workspace_id = d.pop("workspace_id", UNSET)

        parent_job = d.pop("parent_job", UNSET)

        script_path = d.pop("script_path", UNSET)

        script_hash = d.pop("script_hash", UNSET)

        _args = d.pop("args", UNSET)
        args: Union[Unset, GetSuspendedJobFlowResponse200JobType0Args]
        if isinstance(_args, Unset):
            args = UNSET
        else:
            args = GetSuspendedJobFlowResponse200JobType0Args.from_dict(_args)

        result = d.pop("result", UNSET)

        logs = d.pop("logs", UNSET)

        deleted = d.pop("deleted", UNSET)

        raw_code = d.pop("raw_code", UNSET)

        canceled_by = d.pop("canceled_by", UNSET)

        canceled_reason = d.pop("canceled_reason", UNSET)

        schedule_path = d.pop("schedule_path", UNSET)

        _flow_status = d.pop("flow_status", UNSET)
        flow_status: Union[Unset, GetSuspendedJobFlowResponse200JobType0FlowStatus]
        if isinstance(_flow_status, Unset):
            flow_status = UNSET
        else:
            flow_status = GetSuspendedJobFlowResponse200JobType0FlowStatus.from_dict(_flow_status)

        _workflow_as_code_status = d.pop("workflow_as_code_status", UNSET)
        workflow_as_code_status: Union[Unset, GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus]
        if isinstance(_workflow_as_code_status, Unset):
            workflow_as_code_status = UNSET
        else:
            workflow_as_code_status = GetSuspendedJobFlowResponse200JobType0WorkflowAsCodeStatus.from_dict(
                _workflow_as_code_status
            )

        _raw_flow = d.pop("raw_flow", UNSET)
        raw_flow: Union[Unset, GetSuspendedJobFlowResponse200JobType0RawFlow]
        if isinstance(_raw_flow, Unset):
            raw_flow = UNSET
        else:
            raw_flow = GetSuspendedJobFlowResponse200JobType0RawFlow.from_dict(_raw_flow)

        _language = d.pop("language", UNSET)
        language: Union[Unset, GetSuspendedJobFlowResponse200JobType0Language]
        if isinstance(_language, Unset):
            language = UNSET
        else:
            language = GetSuspendedJobFlowResponse200JobType0Language(_language)

        mem_peak = d.pop("mem_peak", UNSET)

        priority = d.pop("priority", UNSET)

        labels = cast(List[str], d.pop("labels", UNSET))

        self_wait_time_ms = d.pop("self_wait_time_ms", UNSET)

        aggregate_wait_time_ms = d.pop("aggregate_wait_time_ms", UNSET)

        preprocessed = d.pop("preprocessed", UNSET)

        worker = d.pop("worker", UNSET)

        _type = d.pop("type", UNSET)
        type: Union[Unset, GetSuspendedJobFlowResponse200JobType0Type]
        if isinstance(_type, Unset):
            type = UNSET
        else:
            type = GetSuspendedJobFlowResponse200JobType0Type(_type)

        get_suspended_job_flow_response_200_job_type_0 = cls(
            id=id,
            created_by=created_by,
            created_at=created_at,
            started_at=started_at,
            duration_ms=duration_ms,
            success=success,
            canceled=canceled,
            job_kind=job_kind,
            permissioned_as=permissioned_as,
            is_flow_step=is_flow_step,
            is_skipped=is_skipped,
            email=email,
            visible_to_owner=visible_to_owner,
            tag=tag,
            workspace_id=workspace_id,
            parent_job=parent_job,
            script_path=script_path,
            script_hash=script_hash,
            args=args,
            result=result,
            logs=logs,
            deleted=deleted,
            raw_code=raw_code,
            canceled_by=canceled_by,
            canceled_reason=canceled_reason,
            schedule_path=schedule_path,
            flow_status=flow_status,
            workflow_as_code_status=workflow_as_code_status,
            raw_flow=raw_flow,
            language=language,
            mem_peak=mem_peak,
            priority=priority,
            labels=labels,
            self_wait_time_ms=self_wait_time_ms,
            aggregate_wait_time_ms=aggregate_wait_time_ms,
            preprocessed=preprocessed,
            worker=worker,
            type=type,
        )

        get_suspended_job_flow_response_200_job_type_0.additional_properties = d
        return get_suspended_job_flow_response_200_job_type_0

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
