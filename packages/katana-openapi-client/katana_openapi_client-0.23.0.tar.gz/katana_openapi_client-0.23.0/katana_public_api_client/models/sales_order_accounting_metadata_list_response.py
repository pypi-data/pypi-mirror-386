from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.sales_order_accounting_metadata import SalesOrderAccountingMetadata


T = TypeVar("T", bound="SalesOrderAccountingMetadataListResponse")


@_attrs_define
class SalesOrderAccountingMetadataListResponse:
    """Response containing a list of accounting metadata records linking sales orders to external accounting systems

    Example:
        {'data': [{'id': 2901, 'sales_order_id': 2001, 'fulfillment_id': 2701, 'invoice_id': 'INV-2024-001',
            'integration_type': 'xero', 'created_at': '2024-01-20T17:00:00Z'}]}
    """

    data: Unset | list["SalesOrderAccountingMetadata"] = UNSET
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
        from ..models.sales_order_accounting_metadata import (
            SalesOrderAccountingMetadata,
        )

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SalesOrderAccountingMetadata.from_dict(data_item_data)

            data.append(data_item)

        sales_order_accounting_metadata_list_response = cls(
            data=data,
        )

        sales_order_accounting_metadata_list_response.additional_properties = d
        return sales_order_accounting_metadata_list_response

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
