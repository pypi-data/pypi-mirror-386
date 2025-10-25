from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.delete_completed_job_response_200_raw_flow_failure_module import (
        DeleteCompletedJobResponse200RawFlowFailureModule,
    )
    from ..models.delete_completed_job_response_200_raw_flow_modules_item import (
        DeleteCompletedJobResponse200RawFlowModulesItem,
    )
    from ..models.delete_completed_job_response_200_raw_flow_preprocessor_module import (
        DeleteCompletedJobResponse200RawFlowPreprocessorModule,
    )


T = TypeVar("T", bound="DeleteCompletedJobResponse200RawFlow")


@_attrs_define
class DeleteCompletedJobResponse200RawFlow:
    """
    Attributes:
        modules (List['DeleteCompletedJobResponse200RawFlowModulesItem']):
        failure_module (Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModule]):
        preprocessor_module (Union[Unset, DeleteCompletedJobResponse200RawFlowPreprocessorModule]):
        same_worker (Union[Unset, bool]):
        concurrent_limit (Union[Unset, float]):
        concurrency_key (Union[Unset, str]):
        concurrency_time_window_s (Union[Unset, float]):
        debounce_delay_s (Union[Unset, float]):
        debounce_key (Union[Unset, str]):
        skip_expr (Union[Unset, str]):
        cache_ttl (Union[Unset, float]):
        priority (Union[Unset, float]):
        early_return (Union[Unset, str]):
        chat_input_enabled (Union[Unset, bool]): Whether this flow accepts chat-style input
    """

    modules: List["DeleteCompletedJobResponse200RawFlowModulesItem"]
    failure_module: Union[Unset, "DeleteCompletedJobResponse200RawFlowFailureModule"] = UNSET
    preprocessor_module: Union[Unset, "DeleteCompletedJobResponse200RawFlowPreprocessorModule"] = UNSET
    same_worker: Union[Unset, bool] = UNSET
    concurrent_limit: Union[Unset, float] = UNSET
    concurrency_key: Union[Unset, str] = UNSET
    concurrency_time_window_s: Union[Unset, float] = UNSET
    debounce_delay_s: Union[Unset, float] = UNSET
    debounce_key: Union[Unset, str] = UNSET
    skip_expr: Union[Unset, str] = UNSET
    cache_ttl: Union[Unset, float] = UNSET
    priority: Union[Unset, float] = UNSET
    early_return: Union[Unset, str] = UNSET
    chat_input_enabled: Union[Unset, bool] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        modules = []
        for modules_item_data in self.modules:
            modules_item = modules_item_data.to_dict()

            modules.append(modules_item)

        failure_module: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.failure_module, Unset):
            failure_module = self.failure_module.to_dict()

        preprocessor_module: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.preprocessor_module, Unset):
            preprocessor_module = self.preprocessor_module.to_dict()

        same_worker = self.same_worker
        concurrent_limit = self.concurrent_limit
        concurrency_key = self.concurrency_key
        concurrency_time_window_s = self.concurrency_time_window_s
        debounce_delay_s = self.debounce_delay_s
        debounce_key = self.debounce_key
        skip_expr = self.skip_expr
        cache_ttl = self.cache_ttl
        priority = self.priority
        early_return = self.early_return
        chat_input_enabled = self.chat_input_enabled

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "modules": modules,
            }
        )
        if failure_module is not UNSET:
            field_dict["failure_module"] = failure_module
        if preprocessor_module is not UNSET:
            field_dict["preprocessor_module"] = preprocessor_module
        if same_worker is not UNSET:
            field_dict["same_worker"] = same_worker
        if concurrent_limit is not UNSET:
            field_dict["concurrent_limit"] = concurrent_limit
        if concurrency_key is not UNSET:
            field_dict["concurrency_key"] = concurrency_key
        if concurrency_time_window_s is not UNSET:
            field_dict["concurrency_time_window_s"] = concurrency_time_window_s
        if debounce_delay_s is not UNSET:
            field_dict["debounce_delay_s"] = debounce_delay_s
        if debounce_key is not UNSET:
            field_dict["debounce_key"] = debounce_key
        if skip_expr is not UNSET:
            field_dict["skip_expr"] = skip_expr
        if cache_ttl is not UNSET:
            field_dict["cache_ttl"] = cache_ttl
        if priority is not UNSET:
            field_dict["priority"] = priority
        if early_return is not UNSET:
            field_dict["early_return"] = early_return
        if chat_input_enabled is not UNSET:
            field_dict["chat_input_enabled"] = chat_input_enabled

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.delete_completed_job_response_200_raw_flow_failure_module import (
            DeleteCompletedJobResponse200RawFlowFailureModule,
        )
        from ..models.delete_completed_job_response_200_raw_flow_modules_item import (
            DeleteCompletedJobResponse200RawFlowModulesItem,
        )
        from ..models.delete_completed_job_response_200_raw_flow_preprocessor_module import (
            DeleteCompletedJobResponse200RawFlowPreprocessorModule,
        )

        d = src_dict.copy()
        modules = []
        _modules = d.pop("modules")
        for modules_item_data in _modules:
            modules_item = DeleteCompletedJobResponse200RawFlowModulesItem.from_dict(modules_item_data)

            modules.append(modules_item)

        _failure_module = d.pop("failure_module", UNSET)
        failure_module: Union[Unset, DeleteCompletedJobResponse200RawFlowFailureModule]
        if isinstance(_failure_module, Unset):
            failure_module = UNSET
        else:
            failure_module = DeleteCompletedJobResponse200RawFlowFailureModule.from_dict(_failure_module)

        _preprocessor_module = d.pop("preprocessor_module", UNSET)
        preprocessor_module: Union[Unset, DeleteCompletedJobResponse200RawFlowPreprocessorModule]
        if isinstance(_preprocessor_module, Unset):
            preprocessor_module = UNSET
        else:
            preprocessor_module = DeleteCompletedJobResponse200RawFlowPreprocessorModule.from_dict(_preprocessor_module)

        same_worker = d.pop("same_worker", UNSET)

        concurrent_limit = d.pop("concurrent_limit", UNSET)

        concurrency_key = d.pop("concurrency_key", UNSET)

        concurrency_time_window_s = d.pop("concurrency_time_window_s", UNSET)

        debounce_delay_s = d.pop("debounce_delay_s", UNSET)

        debounce_key = d.pop("debounce_key", UNSET)

        skip_expr = d.pop("skip_expr", UNSET)

        cache_ttl = d.pop("cache_ttl", UNSET)

        priority = d.pop("priority", UNSET)

        early_return = d.pop("early_return", UNSET)

        chat_input_enabled = d.pop("chat_input_enabled", UNSET)

        delete_completed_job_response_200_raw_flow = cls(
            modules=modules,
            failure_module=failure_module,
            preprocessor_module=preprocessor_module,
            same_worker=same_worker,
            concurrent_limit=concurrent_limit,
            concurrency_key=concurrency_key,
            concurrency_time_window_s=concurrency_time_window_s,
            debounce_delay_s=debounce_delay_s,
            debounce_key=debounce_key,
            skip_expr=skip_expr,
            cache_ttl=cache_ttl,
            priority=priority,
            early_return=early_return,
            chat_input_enabled=chat_input_enabled,
        )

        delete_completed_job_response_200_raw_flow.additional_properties = d
        return delete_completed_job_response_200_raw_flow

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
