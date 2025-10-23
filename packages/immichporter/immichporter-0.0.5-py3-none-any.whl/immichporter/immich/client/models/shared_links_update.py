from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SharedLinksUpdate")


@_attrs_define
class SharedLinksUpdate:
    """
    Attributes:
        enabled (Union[Unset, bool]):
        sidebar_web (Union[Unset, bool]):
    """

    enabled: Union[Unset, bool] = UNSET
    sidebar_web: Union[Unset, bool] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        enabled = self.enabled

        sidebar_web = self.sidebar_web

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if enabled is not UNSET:
            field_dict["enabled"] = enabled
        if sidebar_web is not UNSET:
            field_dict["sidebarWeb"] = sidebar_web

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        enabled = d.pop("enabled", UNSET)

        sidebar_web = d.pop("sidebarWeb", UNSET)

        shared_links_update = cls(
            enabled=enabled,
            sidebar_web=sidebar_web,
        )

        shared_links_update.additional_properties = d
        return shared_links_update

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
