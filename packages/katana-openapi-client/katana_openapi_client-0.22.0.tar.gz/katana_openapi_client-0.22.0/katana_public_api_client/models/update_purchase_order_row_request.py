import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from dateutil.parser import isoparse

from ..client_types import UNSET, Unset

T = TypeVar("T", bound="UpdatePurchaseOrderRowRequest")


@_attrs_define
class UpdatePurchaseOrderRowRequest:
    """Request payload for updating an existing purchase order line item's details and status

    Example:
        {'quantity': 275, 'price_per_unit': 2.95, 'purchase_uom': 'kg', 'received_date': '2024-02-15T14:30:00Z',
            'arrival_date': '2024-02-15T10:00:00Z'}
    """

    quantity: Unset | float = UNSET
    variant_id: Unset | int = UNSET
    tax_rate_id: Unset | int = UNSET
    group_id: Unset | int = UNSET
    price_per_unit: Unset | float = UNSET
    purchase_uom_conversion_rate: Unset | float = UNSET
    purchase_uom: Unset | str = UNSET
    received_date: Unset | datetime.datetime = UNSET
    arrival_date: Unset | datetime.datetime = UNSET

    def to_dict(self) -> dict[str, Any]:
        quantity = self.quantity

        variant_id = self.variant_id

        tax_rate_id = self.tax_rate_id

        group_id = self.group_id

        price_per_unit = self.price_per_unit

        purchase_uom_conversion_rate = self.purchase_uom_conversion_rate

        purchase_uom = self.purchase_uom

        received_date: Unset | str = UNSET
        if not isinstance(self.received_date, Unset):
            received_date = self.received_date.isoformat()

        arrival_date: Unset | str = UNSET
        if not isinstance(self.arrival_date, Unset):
            arrival_date = self.arrival_date.isoformat()

        field_dict: dict[str, Any] = {}

        field_dict.update({})
        if quantity is not UNSET:
            field_dict["quantity"] = quantity
        if variant_id is not UNSET:
            field_dict["variant_id"] = variant_id
        if tax_rate_id is not UNSET:
            field_dict["tax_rate_id"] = tax_rate_id
        if group_id is not UNSET:
            field_dict["group_id"] = group_id
        if price_per_unit is not UNSET:
            field_dict["price_per_unit"] = price_per_unit
        if purchase_uom_conversion_rate is not UNSET:
            field_dict["purchase_uom_conversion_rate"] = purchase_uom_conversion_rate
        if purchase_uom is not UNSET:
            field_dict["purchase_uom"] = purchase_uom
        if received_date is not UNSET:
            field_dict["received_date"] = received_date
        if arrival_date is not UNSET:
            field_dict["arrival_date"] = arrival_date

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        quantity = d.pop("quantity", UNSET)

        variant_id = d.pop("variant_id", UNSET)

        tax_rate_id = d.pop("tax_rate_id", UNSET)

        group_id = d.pop("group_id", UNSET)

        price_per_unit = d.pop("price_per_unit", UNSET)

        purchase_uom_conversion_rate = d.pop("purchase_uom_conversion_rate", UNSET)

        purchase_uom = d.pop("purchase_uom", UNSET)

        _received_date = d.pop("received_date", UNSET)
        received_date: Unset | datetime.datetime
        if isinstance(_received_date, Unset):
            received_date = UNSET
        else:
            received_date = isoparse(_received_date)

        _arrival_date = d.pop("arrival_date", UNSET)
        arrival_date: Unset | datetime.datetime
        if isinstance(_arrival_date, Unset):
            arrival_date = UNSET
        else:
            arrival_date = isoparse(_arrival_date)

        update_purchase_order_row_request = cls(
            quantity=quantity,
            variant_id=variant_id,
            tax_rate_id=tax_rate_id,
            group_id=group_id,
            price_per_unit=price_per_unit,
            purchase_uom_conversion_rate=purchase_uom_conversion_rate,
            purchase_uom=purchase_uom,
            received_date=received_date,
            arrival_date=arrival_date,
        )

        return update_purchase_order_row_request
