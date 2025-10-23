from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validate_library_import_path_response_dto import (
        ValidateLibraryImportPathResponseDto,
    )


T = TypeVar("T", bound="ValidateLibraryResponseDto")


@_attrs_define
class ValidateLibraryResponseDto:
    """
    Attributes:
        import_paths (Union[Unset, list['ValidateLibraryImportPathResponseDto']]):
    """

    import_paths: Union[Unset, list["ValidateLibraryImportPathResponseDto"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        import_paths: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.import_paths, Unset):
            import_paths = []
            for import_paths_item_data in self.import_paths:
                import_paths_item = import_paths_item_data.to_dict()
                import_paths.append(import_paths_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if import_paths is not UNSET:
            field_dict["importPaths"] = import_paths

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validate_library_import_path_response_dto import (
            ValidateLibraryImportPathResponseDto,
        )

        d = dict(src_dict)
        import_paths = []
        _import_paths = d.pop("importPaths", UNSET)
        for import_paths_item_data in _import_paths or []:
            import_paths_item = ValidateLibraryImportPathResponseDto.from_dict(
                import_paths_item_data
            )

            import_paths.append(import_paths_item)

        validate_library_response_dto = cls(
            import_paths=import_paths,
        )

        validate_library_response_dto.additional_properties = d
        return validate_library_response_dto

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
