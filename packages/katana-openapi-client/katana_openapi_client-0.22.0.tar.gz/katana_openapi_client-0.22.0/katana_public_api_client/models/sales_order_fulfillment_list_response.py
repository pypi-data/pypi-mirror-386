from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_fulfillment import SalesOrderFulfillment


T = TypeVar("T", bound="SalesOrderFulfillmentListResponse")


@_attrs_define
class SalesOrderFulfillmentListResponse:
    """Response containing a list of fulfillment records showing shipping and delivery status for sales orders

    Example:
        {'data': [{'id': 2701, 'sales_order_id': 2001, 'tracking_number': 'UPS1234567890', 'tracking_number_url':
            'https://www.ups.com/track?track=UPS1234567890', 'shipped_date': '2024-01-20T16:30:00Z',
            'estimated_delivery_date': '2024-01-22T14:00:00Z', 'actual_delivery_date': None, 'shipping_cost': 25.99,
            'shipping_method': 'UPS Ground', 'carrier': 'UPS', 'notes': 'Signature required for delivery', 'created_at':
            '2024-01-20T16:30:00Z', 'updated_at': '2024-01-20T16:30:00Z'}]}
    """

    data: Unset | list["SalesOrderFulfillment"] = UNSET
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
        from ..models.sales_order_fulfillment import SalesOrderFulfillment

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesOrderFulfillment.from_dict(data_item_data)

            data.append(data_item)

        sales_order_fulfillment_list_response = cls(
            data=data,
        )

        sales_order_fulfillment_list_response.additional_properties = d
        return sales_order_fulfillment_list_response

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
