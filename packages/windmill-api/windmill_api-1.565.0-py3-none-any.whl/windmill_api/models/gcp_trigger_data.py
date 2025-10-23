from typing import TYPE_CHECKING, Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.gcp_trigger_data_delivery_type import GcpTriggerDataDeliveryType
from ..models.gcp_trigger_data_subscription_mode import GcpTriggerDataSubscriptionMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.gcp_trigger_data_delivery_config import GcpTriggerDataDeliveryConfig
    from ..models.gcp_trigger_data_error_handler_args import GcpTriggerDataErrorHandlerArgs
    from ..models.gcp_trigger_data_retry import GcpTriggerDataRetry


T = TypeVar("T", bound="GcpTriggerData")


@_attrs_define
class GcpTriggerData:
    """
    Attributes:
        gcp_resource_path (str):
        subscription_mode (GcpTriggerDataSubscriptionMode): The mode of subscription. 'existing' means using an existing
            GCP subscription, while 'create_update' involves creating or updating a new subscription.
        topic_id (str):
        path (str):
        script_path (str):
        is_flow (bool):
        subscription_id (Union[Unset, str]):
        base_endpoint (Union[Unset, str]):
        delivery_type (Union[Unset, GcpTriggerDataDeliveryType]):
        delivery_config (Union[Unset, GcpTriggerDataDeliveryConfig]):
        enabled (Union[Unset, bool]):
        auto_acknowledge_msg (Union[Unset, bool]):
        ack_deadline (Union[Unset, int]): Time in seconds within which the message must be acknowledged. If not
            provided, defaults to the subscription's acknowledgment deadline (600 seconds).
        error_handler_path (Union[Unset, str]):
        error_handler_args (Union[Unset, GcpTriggerDataErrorHandlerArgs]): The arguments to pass to the script or flow
        retry (Union[Unset, GcpTriggerDataRetry]):
    """

    gcp_resource_path: str
    subscription_mode: GcpTriggerDataSubscriptionMode
    topic_id: str
    path: str
    script_path: str
    is_flow: bool
    subscription_id: Union[Unset, str] = UNSET
    base_endpoint: Union[Unset, str] = UNSET
    delivery_type: Union[Unset, GcpTriggerDataDeliveryType] = UNSET
    delivery_config: Union[Unset, "GcpTriggerDataDeliveryConfig"] = UNSET
    enabled: Union[Unset, bool] = UNSET
    auto_acknowledge_msg: Union[Unset, bool] = UNSET
    ack_deadline: Union[Unset, int] = UNSET
    error_handler_path: Union[Unset, str] = UNSET
    error_handler_args: Union[Unset, "GcpTriggerDataErrorHandlerArgs"] = UNSET
    retry: Union[Unset, "GcpTriggerDataRetry"] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        gcp_resource_path = self.gcp_resource_path
        subscription_mode = self.subscription_mode.value

        topic_id = self.topic_id
        path = self.path
        script_path = self.script_path
        is_flow = self.is_flow
        subscription_id = self.subscription_id
        base_endpoint = self.base_endpoint
        delivery_type: Union[Unset, str] = UNSET
        if not isinstance(self.delivery_type, Unset):
            delivery_type = self.delivery_type.value

        delivery_config: Union[Unset, Dict[str, Any]] = UNSET
        if not isinstance(self.delivery_config, Unset):
            delivery_config = self.delivery_config.to_dict()

        enabled = self.enabled
        auto_acknowledge_msg = self.auto_acknowledge_msg
        ack_deadline = self.ack_deadline
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
                "gcp_resource_path": gcp_resource_path,
                "subscription_mode": subscription_mode,
                "topic_id": topic_id,
                "path": path,
                "script_path": script_path,
                "is_flow": is_flow,
            }
        )
        if subscription_id is not UNSET:
            field_dict["subscription_id"] = subscription_id
        if base_endpoint is not UNSET:
            field_dict["base_endpoint"] = base_endpoint
        if delivery_type is not UNSET:
            field_dict["delivery_type"] = delivery_type
        if delivery_config is not UNSET:
            field_dict["delivery_config"] = delivery_config
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if auto_acknowledge_msg is not UNSET:
            field_dict["auto_acknowledge_msg"] = auto_acknowledge_msg
        if ack_deadline is not UNSET:
            field_dict["ack_deadline"] = ack_deadline
        if error_handler_path is not UNSET:
            field_dict["error_handler_path"] = error_handler_path
        if error_handler_args is not UNSET:
            field_dict["error_handler_args"] = error_handler_args
        if retry is not UNSET:
            field_dict["retry"] = retry

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        from ..models.gcp_trigger_data_delivery_config import GcpTriggerDataDeliveryConfig
        from ..models.gcp_trigger_data_error_handler_args import GcpTriggerDataErrorHandlerArgs
        from ..models.gcp_trigger_data_retry import GcpTriggerDataRetry

        d = src_dict.copy()
        gcp_resource_path = d.pop("gcp_resource_path")

        subscription_mode = GcpTriggerDataSubscriptionMode(d.pop("subscription_mode"))

        topic_id = d.pop("topic_id")

        path = d.pop("path")

        script_path = d.pop("script_path")

        is_flow = d.pop("is_flow")

        subscription_id = d.pop("subscription_id", UNSET)

        base_endpoint = d.pop("base_endpoint", UNSET)

        _delivery_type = d.pop("delivery_type", UNSET)
        delivery_type: Union[Unset, GcpTriggerDataDeliveryType]
        if isinstance(_delivery_type, Unset):
            delivery_type = UNSET
        else:
            delivery_type = GcpTriggerDataDeliveryType(_delivery_type)

        _delivery_config = d.pop("delivery_config", UNSET)
        delivery_config: Union[Unset, GcpTriggerDataDeliveryConfig]
        if isinstance(_delivery_config, Unset):
            delivery_config = UNSET
        else:
            delivery_config = GcpTriggerDataDeliveryConfig.from_dict(_delivery_config)

        enabled = d.pop("enabled", UNSET)

        auto_acknowledge_msg = d.pop("auto_acknowledge_msg", UNSET)

        ack_deadline = d.pop("ack_deadline", UNSET)

        error_handler_path = d.pop("error_handler_path", UNSET)

        _error_handler_args = d.pop("error_handler_args", UNSET)
        error_handler_args: Union[Unset, GcpTriggerDataErrorHandlerArgs]
        if isinstance(_error_handler_args, Unset):
            error_handler_args = UNSET
        else:
            error_handler_args = GcpTriggerDataErrorHandlerArgs.from_dict(_error_handler_args)

        _retry = d.pop("retry", UNSET)
        retry: Union[Unset, GcpTriggerDataRetry]
        if isinstance(_retry, Unset):
            retry = UNSET
        else:
            retry = GcpTriggerDataRetry.from_dict(_retry)

        gcp_trigger_data = cls(
            gcp_resource_path=gcp_resource_path,
            subscription_mode=subscription_mode,
            topic_id=topic_id,
            path=path,
            script_path=script_path,
            is_flow=is_flow,
            subscription_id=subscription_id,
            base_endpoint=base_endpoint,
            delivery_type=delivery_type,
            delivery_config=delivery_config,
            enabled=enabled,
            auto_acknowledge_msg=auto_acknowledge_msg,
            ack_deadline=ack_deadline,
            error_handler_path=error_handler_path,
            error_handler_args=error_handler_args,
            retry=retry,
        )

        gcp_trigger_data.additional_properties = d
        return gcp_trigger_data

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
