from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.service import Service


T = TypeVar("T", bound="ServiceListResponse")


@_attrs_define
class ServiceListResponse:
    """Response containing a list of services available for purchase orders and operations

    Example:
        {'data': [{'id': 401, 'name': 'Assembly Service', 'uom': 'hours', 'category_name': 'Manufacturing Services',
            'is_sellable': True, 'type': 'service', 'additional_info': 'Professional product assembly service',
            'custom_field_collection_id': 1, 'variants': [{'id': 4001, 'sku': 'ASSM-001', 'sales_price': 75.0,
            'default_cost': 50.0, 'service_id': 401, 'type': 'service', 'custom_fields': [{'field_name': 'Skill Level',
            'field_value': 'Expert'}], 'created_at': '2023-10-01T09:00:00Z', 'updated_at': '2023-10-01T09:00:00Z',
            'deleted_at': None}], 'created_at': '2023-10-01T09:00:00Z', 'updated_at': '2023-10-01T09:00:00Z', 'archived_at':
            None, 'deleted_at': None}]}
    """

    data: Unset | list["Service"] = UNSET
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
        from ..models.service import Service

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Service.from_dict(data_item_data)

            data.append(data_item)

        service_list_response = cls(
            data=data,
        )

        service_list_response.additional_properties = d
        return service_list_response

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
