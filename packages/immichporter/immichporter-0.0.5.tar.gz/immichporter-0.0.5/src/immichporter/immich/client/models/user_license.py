import datetime
from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

T = TypeVar("T", bound="UserLicense")


@_attrs_define
class UserLicense:
    """
    Attributes:
        activated_at (datetime.datetime):
        activation_key (str):
        license_key (str):
    """

    activated_at: datetime.datetime
    activation_key: str
    license_key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        activated_at = self.activated_at.isoformat()

        activation_key = self.activation_key

        license_key = self.license_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "activatedAt": activated_at,
                "activationKey": activation_key,
                "licenseKey": license_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        activated_at = isoparse(d.pop("activatedAt"))

        activation_key = d.pop("activationKey")

        license_key = d.pop("licenseKey")

        user_license = cls(
            activated_at=activated_at,
            activation_key=activation_key,
            license_key=license_key,
        )

        user_license.additional_properties = d
        return user_license

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
