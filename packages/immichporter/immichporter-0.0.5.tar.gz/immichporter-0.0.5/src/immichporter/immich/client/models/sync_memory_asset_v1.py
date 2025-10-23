from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="SyncMemoryAssetV1")


@_attrs_define
class SyncMemoryAssetV1:
    """
    Attributes:
        asset_id (str):
        memory_id (str):
    """

    asset_id: str
    memory_id: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        asset_id = self.asset_id

        memory_id = self.memory_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assetId": asset_id,
                "memoryId": memory_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        asset_id = d.pop("assetId")

        memory_id = d.pop("memoryId")

        sync_memory_asset_v1 = cls(
            asset_id=asset_id,
            memory_id=memory_id,
        )

        sync_memory_asset_v1.additional_properties = d
        return sync_memory_asset_v1

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
