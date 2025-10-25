from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.webhook import Webhook


T = TypeVar("T", bound="WebhookListResponse")


@_attrs_define
class WebhookListResponse:
    """List of webhook subscriptions configured for event notifications

    Example:
        {'data': [{'id': 1, 'url': 'https://api.customer.com/webhooks/katana', 'token': 'whk_live_abc123def456',
            'enabled': True, 'description': 'ERP integration webhook for inventory sync', 'subscribed_events':
            ['sales_order.created', 'sales_order.updated', 'current_inventory.product_updated'], 'created_at':
            '2024-01-10T09:00:00Z', 'updated_at': '2024-01-15T11:30:00Z'}, {'id': 2, 'url':
            'https://reporting.company.com/katana-events', 'token': 'whk_live_xyz789', 'enabled': False, 'description':
            'Business intelligence reporting', 'subscribed_events': ['manufacturing_order.done', 'purchase_order.received'],
            'created_at': '2024-01-12T14:00:00Z', 'updated_at': '2024-01-14T16:45:00Z'}]}
    """

    data: Unset | list["Webhook"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        data: Unset | list[dict[str, Any]] = UNSET
        if not isinstance(self.data, Unset):
            data = []
            for data_item_data in self.data:
                data_item = data_item_data.to_dict()
                data.append(data_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.webhook import Webhook

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Webhook.from_dict(data_item_data)

            data.append(data_item)

        webhook_list_response = cls(
            data=data,
        )

        webhook_list_response.additional_properties = d
        return webhook_list_response

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
