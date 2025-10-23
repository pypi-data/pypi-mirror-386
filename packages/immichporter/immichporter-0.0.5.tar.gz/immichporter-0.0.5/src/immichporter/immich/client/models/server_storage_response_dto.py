from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="ServerStorageResponseDto")


@_attrs_define
class ServerStorageResponseDto:
    """
    Attributes:
        disk_available (str):
        disk_available_raw (int):
        disk_size (str):
        disk_size_raw (int):
        disk_usage_percentage (float):
        disk_use (str):
        disk_use_raw (int):
    """

    disk_available: str
    disk_available_raw: int
    disk_size: str
    disk_size_raw: int
    disk_usage_percentage: float
    disk_use: str
    disk_use_raw: int
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        disk_available = self.disk_available

        disk_available_raw = self.disk_available_raw

        disk_size = self.disk_size

        disk_size_raw = self.disk_size_raw

        disk_usage_percentage = self.disk_usage_percentage

        disk_use = self.disk_use

        disk_use_raw = self.disk_use_raw

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "diskAvailable": disk_available,
                "diskAvailableRaw": disk_available_raw,
                "diskSize": disk_size,
                "diskSizeRaw": disk_size_raw,
                "diskUsagePercentage": disk_usage_percentage,
                "diskUse": disk_use,
                "diskUseRaw": disk_use_raw,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        disk_available = d.pop("diskAvailable")

        disk_available_raw = d.pop("diskAvailableRaw")

        disk_size = d.pop("diskSize")

        disk_size_raw = d.pop("diskSizeRaw")

        disk_usage_percentage = d.pop("diskUsagePercentage")

        disk_use = d.pop("diskUse")

        disk_use_raw = d.pop("diskUseRaw")

        server_storage_response_dto = cls(
            disk_available=disk_available,
            disk_available_raw=disk_available_raw,
            disk_size=disk_size,
            disk_size_raw=disk_size_raw,
            disk_usage_percentage=disk_usage_percentage,
            disk_use=disk_use,
            disk_use_raw=disk_use_raw,
        )

        server_storage_response_dto.additional_properties = d
        return server_storage_response_dto

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
