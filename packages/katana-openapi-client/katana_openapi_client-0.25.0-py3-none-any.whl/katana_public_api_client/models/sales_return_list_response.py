from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_return import SalesReturn


T = TypeVar("T", bound="SalesReturnListResponse")


@_attrs_define
class SalesReturnListResponse:
    """Response containing a list of sales returns with customer refund and return processing information

    Example:
        {'data': [{'id': 3001, 'customer_id': 1001, 'sales_order_id': 2001, 'order_no': 'SR-2023-001',
            'return_location_id': 1, 'status': 'RETURNED', 'currency': 'USD', 'return_date': '2023-10-15T14:30:00Z',
            'order_created_date': '2023-10-10T10:00:00Z', 'additional_info': 'Customer reported damaged items',
            'refund_status': 'PROCESSED'}]}
    """

    data: Unset | list["SalesReturn"] = UNSET
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
        from ..models.sales_return import SalesReturn

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesReturn.from_dict(data_item_data)

            data.append(data_item)

        sales_return_list_response = cls(
            data=data,
        )

        sales_return_list_response.additional_properties = d
        return sales_return_list_response

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
