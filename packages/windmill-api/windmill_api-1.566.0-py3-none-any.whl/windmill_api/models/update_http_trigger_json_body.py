from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.update_http_trigger_json_body_authentication_method import UpdateHttpTriggerJsonBodyAuthenticationMethod
from ..models.update_http_trigger_json_body_http_method import UpdateHttpTriggerJsonBodyHttpMethod
from ..models.update_http_trigger_json_body_request_type import UpdateHttpTriggerJsonBodyRequestType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.update_http_trigger_json_body_error_handler_args import UpdateHttpTriggerJsonBodyErrorHandlerArgs
    from ..models.update_http_trigger_json_body_retry import UpdateHttpTriggerJsonBodyRetry
    from ..models.update_http_trigger_json_body_static_asset_config import UpdateHttpTriggerJsonBodyStaticAssetConfig


T = TypeVar("T", bound="UpdateHttpTriggerJsonBody")


@_attrs_define
class UpdateHttpTriggerJsonBody:
    """
    Attributes:
        path (str):
        script_path (str):
        is_flow (bool):
        http_method (UpdateHttpTriggerJsonBodyHttpMethod):
        authentication_method (UpdateHttpTriggerJsonBodyAuthenticationMethod):
        is_static_website (bool):
        route_path (Union[Unset, str]):
        summary (Union[Unset, str]):
        description (Union[Unset, str]):
        workspaced_route (Union[Unset, bool]):
        static_asset_config (Union[Unset, UpdateHttpTriggerJsonBodyStaticAssetConfig]):
        authentication_resource_path (Union[Unset, str]):
        is_async (Union[Unset, bool]): Deprecated, use request_type instead
        request_type (Union[Unset, UpdateHttpTriggerJsonBodyRequestType]):
        wrap_body (Union[Unset, bool]):
        raw_string (Union[Unset, bool]):
        error_handler_path (Union[Unset, str]):
        error_handler_args (Union[Unset, UpdateHttpTriggerJsonBodyErrorHandlerArgs]): The arguments to pass to the
            script or flow
        retry (Union[Unset, UpdateHttpTriggerJsonBodyRetry]):
    """

    path: str
    script_path: str
    is_flow: bool
    http_method: UpdateHttpTriggerJsonBodyHttpMethod
    authentication_method: UpdateHttpTriggerJsonBodyAuthenticationMethod
    is_static_website: bool
    route_path: Union[Unset, str] = UNSET
    summary: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    workspaced_route: Union[Unset, bool] = UNSET
    static_asset_config: Union[Unset, "UpdateHttpTriggerJsonBodyStaticAssetConfig"] = UNSET
    authentication_resource_path: Union[Unset, str] = UNSET
    is_async: Union[Unset, bool] = UNSET
    request_type: Union[Unset, UpdateHttpTriggerJsonBodyRequestType] = UNSET
    wrap_body: Union[Unset, bool] = UNSET
    raw_string: Union[Unset, bool] = UNSET
    error_handler_path: Union[Unset, str] = UNSET
    error_handler_args: Union[Unset, "UpdateHttpTriggerJsonBodyErrorHandlerArgs"] = UNSET
    retry: Union[Unset, "UpdateHttpTriggerJsonBodyRetry"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        path = self.path
        script_path = self.script_path
        is_flow = self.is_flow
        http_method = self.http_method.value

        authentication_method = self.authentication_method.value

        is_static_website = self.is_static_website
        route_path = self.route_path
        summary = self.summary
        description = self.description
        workspaced_route = self.workspaced_route
        static_asset_config: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.static_asset_config, Unset):
            static_asset_config = self.static_asset_config.to_dict()

        authentication_resource_path = self.authentication_resource_path
        is_async = self.is_async
        request_type: Union[Unset, str] = UNSET
        if not isinstance(self.request_type, Unset):
            request_type = self.request_type.value

        wrap_body = self.wrap_body
        raw_string = self.raw_string
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
                "http_method": http_method,
                "authentication_method": authentication_method,
                "is_static_website": is_static_website,
            }
        )
        if route_path is not UNSET:
            field_dict["route_path"] = route_path
        if summary is not UNSET:
            field_dict["summary"] = summary
        if description is not UNSET:
            field_dict["description"] = description
        if workspaced_route is not UNSET:
            field_dict["workspaced_route"] = workspaced_route
        if static_asset_config is not UNSET:
            field_dict["static_asset_config"] = static_asset_config
        if authentication_resource_path is not UNSET:
            field_dict["authentication_resource_path"] = authentication_resource_path
        if is_async is not UNSET:
            field_dict["is_async"] = is_async
        if request_type is not UNSET:
            field_dict["request_type"] = request_type
        if wrap_body is not UNSET:
            field_dict["wrap_body"] = wrap_body
        if raw_string is not UNSET:
            field_dict["raw_string"] = raw_string
        if error_handler_path is not UNSET:
            field_dict["error_handler_path"] = error_handler_path
        if error_handler_args is not UNSET:
            field_dict["error_handler_args"] = error_handler_args
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.update_http_trigger_json_body_error_handler_args import UpdateHttpTriggerJsonBodyErrorHandlerArgs
        from ..models.update_http_trigger_json_body_retry import UpdateHttpTriggerJsonBodyRetry
        from ..models.update_http_trigger_json_body_static_asset_config import (
            UpdateHttpTriggerJsonBodyStaticAssetConfig,
        )

        d = src_dict.copy()
        path = d.pop("path")

        script_path = d.pop("script_path")

        is_flow = d.pop("is_flow")

        http_method = UpdateHttpTriggerJsonBodyHttpMethod(d.pop("http_method"))

        authentication_method = UpdateHttpTriggerJsonBodyAuthenticationMethod(d.pop("authentication_method"))

        is_static_website = d.pop("is_static_website")

        route_path = d.pop("route_path", UNSET)

        summary = d.pop("summary", UNSET)

        description = d.pop("description", UNSET)

        workspaced_route = d.pop("workspaced_route", UNSET)

        _static_asset_config = d.pop("static_asset_config", UNSET)
        static_asset_config: Union[Unset, UpdateHttpTriggerJsonBodyStaticAssetConfig]
        if isinstance(_static_asset_config, Unset):
            static_asset_config = UNSET
        else:
            static_asset_config = UpdateHttpTriggerJsonBodyStaticAssetConfig.from_dict(_static_asset_config)

        authentication_resource_path = d.pop("authentication_resource_path", UNSET)

        is_async = d.pop("is_async", UNSET)

        _request_type = d.pop("request_type", UNSET)
        request_type: Union[Unset, UpdateHttpTriggerJsonBodyRequestType]
        if isinstance(_request_type, Unset):
            request_type = UNSET
        else:
            request_type = UpdateHttpTriggerJsonBodyRequestType(_request_type)

        wrap_body = d.pop("wrap_body", UNSET)

        raw_string = d.pop("raw_string", UNSET)

        error_handler_path = d.pop("error_handler_path", UNSET)

        _error_handler_args = d.pop("error_handler_args", UNSET)
        error_handler_args: Union[Unset, UpdateHttpTriggerJsonBodyErrorHandlerArgs]
        if isinstance(_error_handler_args, Unset):
            error_handler_args = UNSET
        else:
            error_handler_args = UpdateHttpTriggerJsonBodyErrorHandlerArgs.from_dict(_error_handler_args)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, UpdateHttpTriggerJsonBodyRetry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = UpdateHttpTriggerJsonBodyRetry.from_dict(_retry)

        update_http_trigger_json_body = cls(
            path=path,
            script_path=script_path,
            is_flow=is_flow,
            http_method=http_method,
            authentication_method=authentication_method,
            is_static_website=is_static_website,
            route_path=route_path,
            summary=summary,
            description=description,
            workspaced_route=workspaced_route,
            static_asset_config=static_asset_config,
            authentication_resource_path=authentication_resource_path,
            is_async=is_async,
            request_type=request_type,
            wrap_body=wrap_body,
            raw_string=raw_string,
            error_handler_path=error_handler_path,
            error_handler_args=error_handler_args,
            retry=retry,
        )

        update_http_trigger_json_body.additional_properties = d
        return update_http_trigger_json_body

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
