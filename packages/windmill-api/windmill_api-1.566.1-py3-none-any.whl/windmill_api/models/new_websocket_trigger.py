from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.new_websocket_trigger_error_handler_args import NewWebsocketTriggerErrorHandlerArgs
    from ..models.new_websocket_trigger_filters_item import NewWebsocketTriggerFiltersItem
    from ..models.new_websocket_trigger_initial_messages_item_type_0 import NewWebsocketTriggerInitialMessagesItemType0
    from ..models.new_websocket_trigger_initial_messages_item_type_1 import NewWebsocketTriggerInitialMessagesItemType1
    from ..models.new_websocket_trigger_retry import NewWebsocketTriggerRetry
    from ..models.new_websocket_trigger_url_runnable_args import NewWebsocketTriggerUrlRunnableArgs


T = TypeVar("T", bound="NewWebsocketTrigger")


@_attrs_define
class NewWebsocketTrigger:
    """
    Attributes:
        path (str):
        script_path (str):
        is_flow (bool):
        url (str):
        filters (List['NewWebsocketTriggerFiltersItem']):
        can_return_message (bool):
        can_return_error_result (bool):
        enabled (Union[Unset, bool]):
        initial_messages (Union[Unset, List[Union['NewWebsocketTriggerInitialMessagesItemType0',
            'NewWebsocketTriggerInitialMessagesItemType1']]]):
        url_runnable_args (Union[Unset, NewWebsocketTriggerUrlRunnableArgs]): The arguments to pass to the script or
            flow
        error_handler_path (Union[Unset, str]):
        error_handler_args (Union[Unset, NewWebsocketTriggerErrorHandlerArgs]): The arguments to pass to the script or
            flow
        retry (Union[Unset, NewWebsocketTriggerRetry]):
    """

    path: str
    script_path: str
    is_flow: bool
    url: str
    filters: List["NewWebsocketTriggerFiltersItem"]
    can_return_message: bool
    can_return_error_result: bool
    enabled: Union[Unset, bool] = UNSET
    initial_messages: Union[
        Unset, List[Union["NewWebsocketTriggerInitialMessagesItemType0", "NewWebsocketTriggerInitialMessagesItemType1"]]
    ] = UNSET
    url_runnable_args: Union[Unset, "NewWebsocketTriggerUrlRunnableArgs"] = UNSET
    error_handler_path: Union[Unset, str] = UNSET
    error_handler_args: Union[Unset, "NewWebsocketTriggerErrorHandlerArgs"] = UNSET
    retry: Union[Unset, "NewWebsocketTriggerRetry"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        from ..models.new_websocket_trigger_initial_messages_item_type_0 import (
            NewWebsocketTriggerInitialMessagesItemType0,
        )

        path = self.path
        script_path = self.script_path
        is_flow = self.is_flow
        url = self.url
        filters = []
        for filters_item_data in self.filters:
            filters_item = filters_item_data.to_dict()

            filters.append(filters_item)

        can_return_message = self.can_return_message
        can_return_error_result = self.can_return_error_result
        enabled = self.enabled
        initial_messages: Union[Unset, List[Dict[str, Any]]] = UNSET
        if not isinstance(self.initial_messages, Unset):
            initial_messages = []
            for initial_messages_item_data in self.initial_messages:
                initial_messages_item: Dict[str, Any]

                if isinstance(initial_messages_item_data, NewWebsocketTriggerInitialMessagesItemType0):
                    initial_messages_item = initial_messages_item_data.to_dict()

                else:
                    initial_messages_item = initial_messages_item_data.to_dict()

                initial_messages.append(initial_messages_item)

        url_runnable_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.url_runnable_args, Unset):
            url_runnable_args = self.url_runnable_args.to_dict()

        error_handler_path = self.error_handler_path
        error_handler_args: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.error_handler_args, Unset):
            error_handler_args = self.error_handler_args.to_dict()

        retry: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.retry, Unset):
            retry = self.retry.to_dict()

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "path": path,
                "script_path": script_path,
                "is_flow": is_flow,
                "url": url,
                "filters": filters,
                "can_return_message": can_return_message,
                "can_return_error_result": can_return_error_result,
            }
        )
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if initial_messages is not UNSET:
            field_dict["initial_messages"] = initial_messages
        if url_runnable_args is not UNSET:
            field_dict["url_runnable_args"] = url_runnable_args
        if error_handler_path is not UNSET:
            field_dict["error_handler_path"] = error_handler_path
        if error_handler_args is not UNSET:
            field_dict["error_handler_args"] = error_handler_args
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.new_websocket_trigger_error_handler_args import NewWebsocketTriggerErrorHandlerArgs
        from ..models.new_websocket_trigger_filters_item import NewWebsocketTriggerFiltersItem
        from ..models.new_websocket_trigger_initial_messages_item_type_0 import (
            NewWebsocketTriggerInitialMessagesItemType0,
        )
        from ..models.new_websocket_trigger_initial_messages_item_type_1 import (
            NewWebsocketTriggerInitialMessagesItemType1,
        )
        from ..models.new_websocket_trigger_retry import NewWebsocketTriggerRetry
        from ..models.new_websocket_trigger_url_runnable_args import NewWebsocketTriggerUrlRunnableArgs

        d = src_dict.copy()
        path = d.pop("path")

        script_path = d.pop("script_path")

        is_flow = d.pop("is_flow")

        url = d.pop("url")

        filters = []
        _filters = d.pop("filters")
        for filters_item_data in _filters:
            filters_item = NewWebsocketTriggerFiltersItem.from_dict(filters_item_data)

            filters.append(filters_item)

        can_return_message = d.pop("can_return_message")

        can_return_error_result = d.pop("can_return_error_result")

        enabled = d.pop("enabled", UNSET)

        initial_messages = []
        _initial_messages = d.pop("initial_messages", UNSET)
        for initial_messages_item_data in _initial_messages or []:

            def _parse_initial_messages_item(
                data: object,
            ) -> Union["NewWebsocketTriggerInitialMessagesItemType0", "NewWebsocketTriggerInitialMessagesItemType1"]:
                try:
                    if not isinstance(data, dict):
                        raise TypeError()
                    initial_messages_item_type_0 = NewWebsocketTriggerInitialMessagesItemType0.from_dict(data)

                    return initial_messages_item_type_0
                except:  # noqa: E722
                    pass
                if not isinstance(data, dict):
                    raise TypeError()
                initial_messages_item_type_1 = NewWebsocketTriggerInitialMessagesItemType1.from_dict(data)

                return initial_messages_item_type_1

            initial_messages_item = _parse_initial_messages_item(initial_messages_item_data)

            initial_messages.append(initial_messages_item)

        _url_runnable_args = d.pop("url_runnable_args", UNSET)
        url_runnable_args: Union[Unset, NewWebsocketTriggerUrlRunnableArgs]
        if isinstance(_url_runnable_args, Unset):
            url_runnable_args = UNSET
        else:
            url_runnable_args = NewWebsocketTriggerUrlRunnableArgs.from_dict(_url_runnable_args)

        error_handler_path = d.pop("error_handler_path", UNSET)

        _error_handler_args = d.pop("error_handler_args", UNSET)
        error_handler_args: Union[Unset, NewWebsocketTriggerErrorHandlerArgs]
        if isinstance(_error_handler_args, Unset):
            error_handler_args = UNSET
        else:
            error_handler_args = NewWebsocketTriggerErrorHandlerArgs.from_dict(_error_handler_args)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, NewWebsocketTriggerRetry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = NewWebsocketTriggerRetry.from_dict(_retry)

        new_websocket_trigger = cls(
            path=path,
            script_path=script_path,
            is_flow=is_flow,
            url=url,
            filters=filters,
            can_return_message=can_return_message,
            can_return_error_result=can_return_error_result,
            enabled=enabled,
            initial_messages=initial_messages,
            url_runnable_args=url_runnable_args,
            error_handler_path=error_handler_path,
            error_handler_args=error_handler_args,
            retry=retry,
        )

        new_websocket_trigger.additional_properties = d
        return new_websocket_trigger

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
