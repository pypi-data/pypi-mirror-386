from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionCreateDto")


@_attrs_define
class SessionCreateDto:
    """
    Attributes:
        device_os (Union[Unset, str]):
        device_type (Union[Unset, str]):
        duration (Union[Unset, float]): session duration, in seconds
    """

    device_os: Union[Unset, str] = UNSET
    device_type: Union[Unset, str] = UNSET
    duration: Union[Unset, float] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        device_os = self.device_os

        device_type = self.device_type

        duration = self.duration

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if device_os is not UNSET:
            field_dict["deviceOS"] = device_os
        if device_type is not UNSET:
            field_dict["deviceType"] = device_type
        if duration is not UNSET:
            field_dict["duration"] = duration

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        device_os = d.pop("deviceOS", UNSET)

        device_type = d.pop("deviceType", UNSET)

        duration = d.pop("duration", UNSET)

        session_create_dto = cls(
            device_os=device_os,
            device_type=device_type,
            duration=duration,
        )

        session_create_dto.additional_properties = d
        return session_create_dto

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
