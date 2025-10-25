from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.stocktake_row import StocktakeRow


T = TypeVar("T", bound="StocktakeRowListResponse")


@_attrs_define
class StocktakeRowListResponse:
    """List of individual stocktake row records showing counted quantities for each variant in a stocktake session

    Example:
        {'data': [{'id': 4101, 'stocktake_id': 4001, 'variant_id': 3001, 'expected_quantity': 150.0, 'counted_quantity':
            147.0, 'variance': -3.0, 'notes': 'Minor count difference noted', 'created_at': '2024-01-15T09:30:00.000Z',
            'updated_at': '2024-01-15T09:30:00.000Z'}, {'id': 4102, 'stocktake_id': 4001, 'variant_id': 3002,
            'expected_quantity': 75.0, 'counted_quantity': 75.0, 'variance': 0.0, 'notes': 'Count matches expected',
            'created_at': '2024-01-15T10:15:00.000Z', 'updated_at': '2024-01-15T10:15:00.000Z'}]}
    """

    data: Unset | list["StocktakeRow"] = UNSET
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
        from ..models.stocktake_row import StocktakeRow

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = StocktakeRow.from_dict(data_item_data)

            data.append(data_item)

        stocktake_row_list_response = cls(
            data=data,
        )

        stocktake_row_list_response.additional_properties = d
        return stocktake_row_list_response

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
