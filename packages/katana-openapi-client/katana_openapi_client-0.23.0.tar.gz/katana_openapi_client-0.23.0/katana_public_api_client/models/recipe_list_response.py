from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

from ..client_types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.recipe import Recipe


T = TypeVar("T", bound="RecipeListResponse")


@_attrs_define
class RecipeListResponse:
    """Response containing a list of recipe rows

    Example:
        {'data': [{'id': 'aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee', 'recipe_row_id': 'aaaaaaaa-bbbb-cccc-dddd-
            eeeeeeeeeeee', 'product_item_id': 1, 'product_variant_id': 1, 'ingredient_variant_id': 1, 'quantity': 2,
            'notes': 'some notes', 'rank': 10000, 'created_at': '2021-04-05T12:00:00.000Z', 'updated_at':
            '2021-04-05T12:00:00.000Z'}]}
    """

    data: Unset | list["Recipe"] = UNSET
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
        from ..models.recipe import Recipe

        d = dict(src_dict)
        data = []
        _data = d.pop("data", UNSET)
        for data_item_data in _data or []:
            data_item = Recipe.from_dict(data_item_data)

            data.append(data_item)

        recipe_list_response = cls(
            data=data,
        )

        recipe_list_response.additional_properties = d
        return recipe_list_response

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
