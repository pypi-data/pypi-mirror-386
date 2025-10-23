from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.run_flow_preview_json_body_value_failure_module import RunFlowPreviewJsonBodyValueFailureModule
    from ..models.run_flow_preview_json_body_value_modules_item import RunFlowPreviewJsonBodyValueModulesItem
    from ..models.run_flow_preview_json_body_value_preprocessor_module import (
        RunFlowPreviewJsonBodyValuePreprocessorModule,
    )


T = TypeVar("T", bound="RunFlowPreviewJsonBodyValue")


@_attrs_define
class RunFlowPreviewJsonBodyValue:
    """
    Attributes:
        modules (List['RunFlowPreviewJsonBodyValueModulesItem']):
        failure_module (Union[Unset, RunFlowPreviewJsonBodyValueFailureModule]):
        preprocessor_module (Union[Unset, RunFlowPreviewJsonBodyValuePreprocessorModule]):
        same_worker (Union[Unset, bool]):
        concurrent_limit (Union[Unset, float]):
        concurrency_key (Union[Unset, str]):
        concurrency_time_window_s (Union[Unset, float]):
        skip_expr (Union[Unset, str]):
        cache_ttl (Union[Unset, float]):
        priority (Union[Unset, float]):
        early_return (Union[Unset, str]):
        chat_input_enabled (Union[Unset, bool]): Whether this flow accepts chat-style input
    """

    modules: List["RunFlowPreviewJsonBodyValueModulesItem"]
    failure_module: Union[Unset, "RunFlowPreviewJsonBodyValueFailureModule"] = UNSET
    preprocessor_module: Union[Unset, "RunFlowPreviewJsonBodyValuePreprocessorModule"] = UNSET
    same_worker: Union[Unset, bool] = UNSET
    concurrent_limit: Union[Unset, float] = UNSET
    concurrency_key: Union[Unset, str] = UNSET
    concurrency_time_window_s: Union[Unset, float] = UNSET
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
        from ..models.run_flow_preview_json_body_value_failure_module import RunFlowPreviewJsonBodyValueFailureModule
        from ..models.run_flow_preview_json_body_value_modules_item import RunFlowPreviewJsonBodyValueModulesItem
        from ..models.run_flow_preview_json_body_value_preprocessor_module import (
            RunFlowPreviewJsonBodyValuePreprocessorModule,
        )

        d = src_dict.copy()
        modules = []
        _modules = d.pop("modules")
        for modules_item_data in _modules:
            modules_item = RunFlowPreviewJsonBodyValueModulesItem.from_dict(modules_item_data)

            modules.append(modules_item)

        _failure_module = d.pop("failure_module", UNSET)
        failure_module: Union[Unset, RunFlowPreviewJsonBodyValueFailureModule]
        if isinstance(_failure_module, Unset):
            failure_module = UNSET
        else:
            failure_module = RunFlowPreviewJsonBodyValueFailureModule.from_dict(_failure_module)

        _preprocessor_module = d.pop("preprocessor_module", UNSET)
        preprocessor_module: Union[Unset, RunFlowPreviewJsonBodyValuePreprocessorModule]
        if isinstance(_preprocessor_module, Unset):
            preprocessor_module = UNSET
        else:
            preprocessor_module = RunFlowPreviewJsonBodyValuePreprocessorModule.from_dict(_preprocessor_module)

        same_worker = d.pop("same_worker", UNSET)

        concurrent_limit = d.pop("concurrent_limit", UNSET)

        concurrency_key = d.pop("concurrency_key", UNSET)

        concurrency_time_window_s = d.pop("concurrency_time_window_s", UNSET)

        skip_expr = d.pop("skip_expr", UNSET)

        cache_ttl = d.pop("cache_ttl", UNSET)

        priority = d.pop("priority", UNSET)

        early_return = d.pop("early_return", UNSET)

        chat_input_enabled = d.pop("chat_input_enabled", UNSET)

        run_flow_preview_json_body_value = cls(
            modules=modules,
            failure_module=failure_module,
            preprocessor_module=preprocessor_module,
            same_worker=same_worker,
            concurrent_limit=concurrent_limit,
            concurrency_key=concurrency_key,
            concurrency_time_window_s=concurrency_time_window_s,
            skip_expr=skip_expr,
            cache_ttl=cache_ttl,
            priority=priority,
            early_return=early_return,
            chat_input_enabled=chat_input_enabled,
        )

        run_flow_preview_json_body_value.additional_properties = d
        return run_flow_preview_json_body_value

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
