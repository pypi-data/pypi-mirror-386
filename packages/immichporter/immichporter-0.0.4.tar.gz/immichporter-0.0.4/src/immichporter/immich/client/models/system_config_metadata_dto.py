from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.system_config_faces_dto import SystemConfigFacesDto


T = TypeVar("T", bound="SystemConfigMetadataDto")


@_attrs_define
class SystemConfigMetadataDto:
    """
    Attributes:
        faces (SystemConfigFacesDto):
    """

    faces: "SystemConfigFacesDto"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        faces = self.faces.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "faces": faces,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.system_config_faces_dto import SystemConfigFacesDto

        d = dict(src_dict)
        faces = SystemConfigFacesDto.from_dict(d.pop("faces"))

        system_config_metadata_dto = cls(
            faces=faces,
        )

        system_config_metadata_dto.additional_properties = d
        return system_config_metadata_dto

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
