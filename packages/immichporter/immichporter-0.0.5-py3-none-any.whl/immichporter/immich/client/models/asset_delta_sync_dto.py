import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="AssetDeltaSyncDto")


@_attrs_define
class AssetDeltaSyncDto:
    """
    Attributes:
        updated_after (datetime.datetime):
        user_ids (list[UUID]):
    """

    updated_after: datetime.datetime
    user_ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        updated_after = self.updated_after.isoformat()

        user_ids = []
        for user_ids_item_data in self.user_ids:
            user_ids_item = str(user_ids_item_data)
            user_ids.append(user_ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "updatedAfter": updated_after,
                "userIds": user_ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        updated_after = isoparse(d.pop("updatedAfter"))

        user_ids = []
        _user_ids = d.pop("userIds")
        for user_ids_item_data in _user_ids:
            user_ids_item = UUID(user_ids_item_data)

            user_ids.append(user_ids_item)

        asset_delta_sync_dto = cls(
            updated_after=updated_after,
            user_ids=user_ids,
        )

        asset_delta_sync_dto.additional_properties = d
        return asset_delta_sync_dto

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
