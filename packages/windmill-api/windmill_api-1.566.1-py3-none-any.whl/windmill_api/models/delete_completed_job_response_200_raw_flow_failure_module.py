from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_mock import (
        DeleteCompletedJobResponse200RawFlowFailureModuleMock,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_retry import (
        DeleteCompletedJobResponse200RawFlowFailureModuleRetry,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_skip_if import (
        DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_sleep_type_0 import (
        DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_sleep_type_1 import (
        DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_stop_after_all_iters_if import (
        DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_stop_after_if import (
        DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_suspend import (
        DeleteCompletedJobResponse200RawFlowFailureModuleSuspend,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_timeout_type_0 import (
        DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0,
    )
    from ..models.delete_completed_job_response_200_raw_flow_failure_module_timeout_type_1 import (
        DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1,
    )


T = TypeVar("T", bound="DeleteCompletedJobResponse200RawFlowFailureModule")


@_attrs_define
class DeleteCompletedJobResponse200RawFlowFailureModule:
    """
    Attributes:
        id (str):
        value (Any):
        stop_after_if (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf]):
        stop_after_all_iters_if (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf]):
        skip_if (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf]):
        sleep (Union['DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0',
            'DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1', Unset]):
        cache_ttl (Union[Unset, float]):
        timeout (Union['DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0',
            'DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1', Unset]):
        delete_after_use (Union[Unset, bool]):
        summary (Union[Unset, str]):
        mock (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleMock]):
        suspend (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSuspend]):
        priority (Union[Unset, float]):
        continue_on_error (Union[Unset, bool]):
        retry (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleRetry]):
    """

    id: str
    value: Any
    stop_after_if: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf"] = UNSET
    stop_after_all_iters_if: Union[
        Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf"
    ] = UNSET
    skip_if: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf"] = UNSET
    sleep: Union[
        "DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0",
        "DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1",
        Unset,
    ] = UNSET
    cache_ttl: Union[Unset, float] = UNSET
    timeout: Union[
        "DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0",
        "DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1",
        Unset,
    ] = UNSET
    delete_after_use: Union[Unset, bool] = UNSET
    summary: Union[Unset, str] = UNSET
    mock: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleMock"] = UNSET
    suspend: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleSuspend"] = UNSET
    priority: Union[Unset, float] = UNSET
    continue_on_error: Union[Unset, bool] = UNSET
    retry: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModuleRetry"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_sleep_type_0 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_timeout_type_0 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0,
        )

        id = self.id
        value = self.value
        stop_after_if: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.stop_after_if, Unset):
            stop_after_if = self.stop_after_if.to_dict()

        stop_after_all_iters_if: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.stop_after_all_iters_if, Unset):
            stop_after_all_iters_if = self.stop_after_all_iters_if.to_dict()

        skip_if: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.skip_if, Unset):
            skip_if = self.skip_if.to_dict()

        sleep: Union[Dict[str, Any], Unset]
        if isinstance(self.sleep, Unset):
            sleep = UNSET

        elif isinstance(self.sleep, DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0):
            sleep = UNSET
            if not isinstance(self.sleep, Unset):
                sleep = self.sleep.to_dict()

        else:
            sleep = UNSET
            if not isinstance(self.sleep, Unset):
                sleep = self.sleep.to_dict()

        cache_ttl = self.cache_ttl
        timeout: Union[Dict[str, Any], Unset]
        if isinstance(self.timeout, Unset):
            timeout = UNSET

        elif isinstance(self.timeout, DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0):
            timeout = UNSET
            if not isinstance(self.timeout, Unset):
                timeout = self.timeout.to_dict()

        else:
            timeout = UNSET
            if not isinstance(self.timeout, Unset):
                timeout = self.timeout.to_dict()

        delete_after_use = self.delete_after_use
        summary = self.summary
        mock: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.mock, Unset):
            mock = self.mock.to_dict()

        suspend: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.suspend, Unset):
            suspend = self.suspend.to_dict()

        priority = self.priority
        continue_on_error = self.continue_on_error
        retry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.retry, Unset):
            retry = self.retry.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "value": value,
            }
        )
        if stop_after_if is not UNSET:
            field_dict["stop_after_if"] = stop_after_if
        if stop_after_all_iters_if is not UNSET:
            field_dict["stop_after_all_iters_if"] = stop_after_all_iters_if
        if skip_if is not UNSET:
            field_dict["skip_if"] = skip_if
        if sleep is not UNSET:
            field_dict["sleep"] = sleep
        if cache_ttl is not UNSET:
            field_dict["cache_ttl"] = cache_ttl
        if timeout is not UNSET:
            field_dict["timeout"] = timeout
        if delete_after_use is not UNSET:
            field_dict["delete_after_use"] = delete_after_use
        if summary is not UNSET:
            field_dict["summary"] = summary
        if mock is not UNSET:
            field_dict["mock"] = mock
        if suspend is not UNSET:
            field_dict["suspend"] = suspend
        if priority is not UNSET:
            field_dict["priority"] = priority
        if continue_on_error is not UNSET:
            field_dict["continue_on_error"] = continue_on_error
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_mock import (
            DeleteCompletedJobResponse200RawFlowFailureModuleMock,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_retry import (
            DeleteCompletedJobResponse200RawFlowFailureModuleRetry,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_skip_if import (
            DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_sleep_type_0 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_sleep_type_1 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_stop_after_all_iters_if import (
            DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_stop_after_if import (
            DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_suspend import (
            DeleteCompletedJobResponse200RawFlowFailureModuleSuspend,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_timeout_type_0 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0,
        )
        from ..models.delete_completed_job_response_200_raw_flow_failure_module_timeout_type_1 import (
            DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1,
        )

        d = src_dict.copy()
        id = d.pop("id")

        value = d.pop("value")

        _stop_after_if = d.pop("stop_after_if", UNSET)
        stop_after_if: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf]
        if isinstance(_stop_after_if, Unset):
            stop_after_if = UNSET
        else:
            stop_after_if = DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterIf.from_dict(_stop_after_if)

        _stop_after_all_iters_if = d.pop("stop_after_all_iters_if", UNSET)
        stop_after_all_iters_if: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf]
        if isinstance(_stop_after_all_iters_if, Unset):
            stop_after_all_iters_if = UNSET
        else:
            stop_after_all_iters_if = DeleteCompletedJobResponse200RawFlowFailureModuleStopAfterAllItersIf.from_dict(
                _stop_after_all_iters_if
            )

        _skip_if = d.pop("skip_if", UNSET)
        skip_if: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf]
        if isinstance(_skip_if, Unset):
            skip_if = UNSET
        else:
            skip_if = DeleteCompletedJobResponse200RawFlowFailureModuleSkipIf.from_dict(_skip_if)

        def _parse_sleep(
            data: object,
        ) -> Union[
            "DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0",
            "DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _sleep_type_0 = data
                sleep_type_0: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0]
                if isinstance(_sleep_type_0, Unset):
                    sleep_type_0 = UNSET
                else:
                    sleep_type_0 = DeleteCompletedJobResponse200RawFlowFailureModuleSleepType0.from_dict(_sleep_type_0)

                return sleep_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _sleep_type_1 = data
            sleep_type_1: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1]
            if isinstance(_sleep_type_1, Unset):
                sleep_type_1 = UNSET
            else:
                sleep_type_1 = DeleteCompletedJobResponse200RawFlowFailureModuleSleepType1.from_dict(_sleep_type_1)

            return sleep_type_1

        sleep = _parse_sleep(d.pop("sleep", UNSET))

        cache_ttl = d.pop("cache_ttl", UNSET)

        def _parse_timeout(
            data: object,
        ) -> Union[
            "DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0",
            "DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1",
            Unset,
        ]:
            if isinstance(data, Unset):
                return data
            try:
                if not isinstance(data, dict):
                    raise TypeError()
                _timeout_type_0 = data
                timeout_type_0: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0]
                if isinstance(_timeout_type_0, Unset):
                    timeout_type_0 = UNSET
                else:
                    timeout_type_0 = DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType0.from_dict(
                        _timeout_type_0
                    )

                return timeout_type_0
            except:  # noqa: E722
                pass
            if not isinstance(data, dict):
                raise TypeError()
            _timeout_type_1 = data
            timeout_type_1: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1]
            if isinstance(_timeout_type_1, Unset):
                timeout_type_1 = UNSET
            else:
                timeout_type_1 = DeleteCompletedJobResponse200RawFlowFailureModuleTimeoutType1.from_dict(
                    _timeout_type_1
                )

            return timeout_type_1

        timeout = _parse_timeout(d.pop("timeout", UNSET))

        delete_after_use = d.pop("delete_after_use", UNSET)

        summary = d.pop("summary", UNSET)

        _mock = d.pop("mock", UNSET)
        mock: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleMock]
        if isinstance(_mock, Unset):
            mock = UNSET
        else:
            mock = DeleteCompletedJobResponse200RawFlowFailureModuleMock.from_dict(_mock)

        _suspend = d.pop("suspend", UNSET)
        suspend: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleSuspend]
        if isinstance(_suspend, Unset):
            suspend = UNSET
        else:
            suspend = DeleteCompletedJobResponse200RawFlowFailureModuleSuspend.from_dict(_suspend)

        priority = d.pop("priority", UNSET)

        continue_on_error = d.pop("continue_on_error", UNSET)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModuleRetry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = DeleteCompletedJobResponse200RawFlowFailureModuleRetry.from_dict(_retry)

        delete_completed_job_response_200_raw_flow_failure_module = cls(
            id=id,
            value=value,
            stop_after_if=stop_after_if,
            stop_after_all_iters_if=stop_after_all_iters_if,
            skip_if=skip_if,
            sleep=sleep,
            cache_ttl=cache_ttl,
            timeout=timeout,
            delete_after_use=delete_after_use,
            summary=summary,
            mock=mock,
            suspend=suspend,
            priority=priority,
            continue_on_error=continue_on_error,
            retry=retry,
        )

        delete_completed_job_response_200_raw_flow_failure_module.additional_properties = d
        return delete_completed_job_response_200_raw_flow_failure_module

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
