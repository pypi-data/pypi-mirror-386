import datetime
from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.edit_schedule_args import EditScheduleArgs
    from ..models.edit_schedule_on_failure_extra_args import EditScheduleOnFailureExtraArgs
    from ..models.edit_schedule_on_recovery_extra_args import EditScheduleOnRecoveryExtraArgs
    from ..models.edit_schedule_on_success_extra_args import EditScheduleOnSuccessExtraArgs
    from ..models.edit_schedule_retry import EditScheduleRetry


T = TypeVar("T", bound="EditSchedule")


@_attrs_define
class EditSchedule:
    """
    Attributes:
        schedule (str): The cron schedule to trigger the script or flow. Should include seconds.
        timezone (str): The timezone to use for the cron schedule
        args (EditScheduleArgs): The arguments to pass to the script or flow
        on_failure (Union[Unset, str]): The path to the script or flow to trigger on failure
        on_failure_times (Union[Unset, float]): The number of times to retry on failure
        on_failure_exact (Union[Unset, bool]): Whether the schedule should only run on the exact time
        on_failure_extra_args (Union[Unset, EditScheduleOnFailureExtraArgs]): The arguments to pass to the script or
            flow
        on_recovery (Union[Unset, str]): The path to the script or flow to trigger on recovery
        on_recovery_times (Union[Unset, float]): The number of times to retry on recovery
        on_recovery_extra_args (Union[Unset, EditScheduleOnRecoveryExtraArgs]): The arguments to pass to the script or
            flow
        on_success (Union[Unset, str]): The path to the script or flow to trigger on success
        on_success_extra_args (Union[Unset, EditScheduleOnSuccessExtraArgs]): The arguments to pass to the script or
            flow
        ws_error_handler_muted (Union[Unset, bool]): Whether the WebSocket error handler is muted
        retry (Union[Unset, EditScheduleRetry]): The retry configuration for the schedule
        no_flow_overlap (Union[Unset, bool]): Whether the schedule should not run if a flow is already running
        summary (Union[Unset, str]): The summary of the schedule
        description (Union[Unset, str]): The description of the schedule
        tag (Union[Unset, str]): The tag of the schedule
        paused_until (Union[Unset, datetime.datetime]): The date and time the schedule will be paused until
        cron_version (Union[Unset, str]): The version of the cron schedule to use (last is v2)
        dynamic_skip (Union[Unset, str]): Path to a script that validates scheduled datetimes. Receives scheduled_for
            datetime and returns boolean.
    """

    schedule: str
    timezone: str
    args: "EditScheduleArgs"
    on_failure: Union[Unset, str] = UNSET
    on_failure_times: Union[Unset, float] = UNSET
    on_failure_exact: Union[Unset, bool] = UNSET
    on_failure_extra_args: Union[Unset, "EditScheduleOnFailureExtraArgs"] = UNSET
    on_recovery: Union[Unset, str] = UNSET
    on_recovery_times: Union[Unset, float] = UNSET
    on_recovery_extra_args: Union[Unset, "EditScheduleOnRecoveryExtraArgs"] = UNSET
    on_success: Union[Unset, str] = UNSET
    on_success_extra_args: Union[Unset, "EditScheduleOnSuccessExtraArgs"] = UNSET
    ws_error_handler_muted: Union[Unset, bool] = UNSET
    retry: Union[Unset, "EditScheduleRetry"] = UNSET
    no_flow_overlap: Union[Unset, bool] = UNSET
    summary: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    tag: Union[Unset, str] = UNSET
    paused_until: Union[Unset, datetime.datetime] = UNSET
    cron_version: Union[Unset, str] = UNSET
    dynamic_skip: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        schedule = self.schedule
        timezone = self.timezone
        args = self.args.to_dict()

        on_failure = self.on_failure
        on_failure_times = self.on_failure_times
        on_failure_exact = self.on_failure_exact
        on_failure_extra_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.on_failure_extra_args, Unset):
            on_failure_extra_args = self.on_failure_extra_args.to_dict()

        on_recovery = self.on_recovery
        on_recovery_times = self.on_recovery_times
        on_recovery_extra_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.on_recovery_extra_args, Unset):
            on_recovery_extra_args = self.on_recovery_extra_args.to_dict()

        on_success = self.on_success
        on_success_extra_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.on_success_extra_args, Unset):
            on_success_extra_args = self.on_success_extra_args.to_dict()

        ws_error_handler_muted = self.ws_error_handler_muted
        retry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.retry, Unset):
            retry = self.retry.to_dict()

        no_flow_overlap = self.no_flow_overlap
        summary = self.summary
        description = self.description
        tag = self.tag
        paused_until: Union[Unset, str] = UNSET
        if not isinstance(self.paused_until, Unset):
            paused_until = self.paused_until.isoformat()

        cron_version = self.cron_version
        dynamic_skip = self.dynamic_skip

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "schedule": schedule,
                "timezone": timezone,
                "args": args,
            }
        )
        if on_failure is not UNSET:
            field_dict["on_failure"] = on_failure
        if on_failure_times is not UNSET:
            field_dict["on_failure_times"] = on_failure_times
        if on_failure_exact is not UNSET:
            field_dict["on_failure_exact"] = on_failure_exact
        if on_failure_extra_args is not UNSET:
            field_dict["on_failure_extra_args"] = on_failure_extra_args
        if on_recovery is not UNSET:
            field_dict["on_recovery"] = on_recovery
        if on_recovery_times is not UNSET:
            field_dict["on_recovery_times"] = on_recovery_times
        if on_recovery_extra_args is not UNSET:
            field_dict["on_recovery_extra_args"] = on_recovery_extra_args
        if on_success is not UNSET:
            field_dict["on_success"] = on_success
        if on_success_extra_args is not UNSET:
            field_dict["on_success_extra_args"] = on_success_extra_args
        if ws_error_handler_muted is not UNSET:
            field_dict["ws_error_handler_muted"] = ws_error_handler_muted
        if retry is not UNSET:
            field_dict["retry"] = retry
        if no_flow_overlap is not UNSET:
            field_dict["no_flow_overlap"] = no_flow_overlap
        if summary is not UNSET:
            field_dict["summary"] = summary
        if description is not UNSET:
            field_dict["description"] = description
        if tag is not UNSET:
            field_dict["tag"] = tag
        if paused_until is not UNSET:
            field_dict["paused_until"] = paused_until
        if cron_version is not UNSET:
            field_dict["cron_version"] = cron_version
        if dynamic_skip is not UNSET:
            field_dict["dynamic_skip"] = dynamic_skip

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.edit_schedule_args import EditScheduleArgs
        from ..models.edit_schedule_on_failure_extra_args import EditScheduleOnFailureExtraArgs
        from ..models.edit_schedule_on_recovery_extra_args import EditScheduleOnRecoveryExtraArgs
        from ..models.edit_schedule_on_success_extra_args import EditScheduleOnSuccessExtraArgs
        from ..models.edit_schedule_retry import EditScheduleRetry

        d = src_dict.copy()
        schedule = d.pop("schedule")

        timezone = d.pop("timezone")

        args = EditScheduleArgs.from_dict(d.pop("args"))

        on_failure = d.pop("on_failure", UNSET)

        on_failure_times = d.pop("on_failure_times", UNSET)

        on_failure_exact = d.pop("on_failure_exact", UNSET)

        _on_failure_extra_args = d.pop("on_failure_extra_args", UNSET)
        on_failure_extra_args: Union[Unset, EditScheduleOnFailureExtraArgs]
        if isinstance(_on_failure_extra_args, Unset):
            on_failure_extra_args = UNSET
        else:
            on_failure_extra_args = EditScheduleOnFailureExtraArgs.from_dict(_on_failure_extra_args)

        on_recovery = d.pop("on_recovery", UNSET)

        on_recovery_times = d.pop("on_recovery_times", UNSET)

        _on_recovery_extra_args = d.pop("on_recovery_extra_args", UNSET)
        on_recovery_extra_args: Union[Unset, EditScheduleOnRecoveryExtraArgs]
        if isinstance(_on_recovery_extra_args, Unset):
            on_recovery_extra_args = UNSET
        else:
            on_recovery_extra_args = EditScheduleOnRecoveryExtraArgs.from_dict(_on_recovery_extra_args)

        on_success = d.pop("on_success", UNSET)

        _on_success_extra_args = d.pop("on_success_extra_args", UNSET)
        on_success_extra_args: Union[Unset, EditScheduleOnSuccessExtraArgs]
        if isinstance(_on_success_extra_args, Unset):
            on_success_extra_args = UNSET
        else:
            on_success_extra_args = EditScheduleOnSuccessExtraArgs.from_dict(_on_success_extra_args)

        ws_error_handler_muted = d.pop("ws_error_handler_muted", UNSET)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, EditScheduleRetry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = EditScheduleRetry.from_dict(_retry)

        no_flow_overlap = d.pop("no_flow_overlap", UNSET)

        summary = d.pop("summary", UNSET)

        description = d.pop("description", UNSET)

        tag = d.pop("tag", UNSET)

        _paused_until = d.pop("paused_until", UNSET)
        paused_until: Union[Unset, datetime.datetime]
        if isinstance(_paused_until, Unset):
            paused_until = UNSET
        else:
            paused_until = isoparse(_paused_until)

        cron_version = d.pop("cron_version", UNSET)

        dynamic_skip = d.pop("dynamic_skip", UNSET)

        edit_schedule = cls(
            schedule=schedule,
            timezone=timezone,
            args=args,
            on_failure=on_failure,
            on_failure_times=on_failure_times,
            on_failure_exact=on_failure_exact,
            on_failure_extra_args=on_failure_extra_args,
            on_recovery=on_recovery,
            on_recovery_times=on_recovery_times,
            on_recovery_extra_args=on_recovery_extra_args,
            on_success=on_success,
            on_success_extra_args=on_success_extra_args,
            ws_error_handler_muted=ws_error_handler_muted,
            retry=retry,
            no_flow_overlap=no_flow_overlap,
            summary=summary,
            description=description,
            tag=tag,
            paused_until=paused_until,
            cron_version=cron_version,
            dynamic_skip=dynamic_skip,
        )

        edit_schedule.additional_properties = d
        return edit_schedule

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
