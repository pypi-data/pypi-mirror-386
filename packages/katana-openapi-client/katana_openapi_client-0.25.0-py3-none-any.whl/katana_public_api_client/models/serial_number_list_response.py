from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.serial_number import SerialNumber


T = TypeVar("T", bound="SerialNumberListResponse")


@_attrs_define
class SerialNumberListResponse:
    """List of serial number records for tracking individual units and enabling full product traceability

    Example:
        {'data': [{'id': 5001, 'serial_number': 'KNF001234567', 'variant_id': 3001, 'location_id': 1, 'status':
            'IN_STOCK', 'created_at': '2024-01-15T08:00:00.000Z', 'updated_at': '2024-01-15T08:00:00.000Z'}, {'id': 5002,
            'serial_number': 'KNF001234568', 'variant_id': 3001, 'location_id': 1, 'status': 'SOLD', 'created_at':
            '2024-01-15T08:30:00.000Z', 'updated_at': '2024-01-16T14:20:00.000Z'}]}
    """

    data: Unset | list["SerialNumber"] = UNSET
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
        from ..models.serial_number import SerialNumber

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = SerialNumber.from_dict(data_item_data)

            data.append(data_item)

        serial_number_list_response = cls(
            data=data,
        )

        serial_number_list_response.additional_properties = d
        return serial_number_list_response

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
