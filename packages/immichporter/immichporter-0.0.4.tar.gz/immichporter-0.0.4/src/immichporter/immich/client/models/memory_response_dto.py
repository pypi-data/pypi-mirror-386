import datetime
from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.memory_type import MemoryType
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.asset_response_dto import AssetResponseDto
    from ..models.on_this_day_dto import OnThisDayDto


T = TypeVar("T", bound="MemoryResponseDto")


@_attrs_define
class MemoryResponseDto:
    """
    Attributes:
        assets (list['AssetResponseDto']):
        created_at (datetime.datetime):
        data (OnThisDayDto):
        id (str):
        is_saved (bool):
        memory_at (datetime.datetime):
        owner_id (str):
        type_ (MemoryType):
        updated_at (datetime.datetime):
        deleted_at (Union[Unset, datetime.datetime]):
        hide_at (Union[Unset, datetime.datetime]):
        seen_at (Union[Unset, datetime.datetime]):
        show_at (Union[Unset, datetime.datetime]):
    """

    assets: list["AssetResponseDto"]
    created_at: datetime.datetime
    data: "OnThisDayDto"
    id: str
    is_saved: bool
    memory_at: datetime.datetime
    owner_id: str
    type_: MemoryType
    updated_at: datetime.datetime
    deleted_at: Union[Unset, datetime.datetime] = UNSET
    hide_at: Union[Unset, datetime.datetime] = UNSET
    seen_at: Union[Unset, datetime.datetime] = UNSET
    show_at: Union[Unset, datetime.datetime] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        assets = []
        for assets_item_data in self.assets:
            assets_item = assets_item_data.to_dict()
            assets.append(assets_item)

        created_at = self.created_at.isoformat()

        data = self.data.to_dict()

        id = self.id

        is_saved = self.is_saved

        memory_at = self.memory_at.isoformat()

        owner_id = self.owner_id

        type_ = self.type_.value

        updated_at = self.updated_at.isoformat()

        deleted_at: Union[Unset, str] = UNSET
        if not isinstance(self.deleted_at, Unset):
            deleted_at = self.deleted_at.isoformat()

        hide_at: Union[Unset, str] = UNSET
        if not isinstance(self.hide_at, Unset):
            hide_at = self.hide_at.isoformat()

        seen_at: Union[Unset, str] = UNSET
        if not isinstance(self.seen_at, Unset):
            seen_at = self.seen_at.isoformat()

        show_at: Union[Unset, str] = UNSET
        if not isinstance(self.show_at, Unset):
            show_at = self.show_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "assets": assets,
                "createdAt": created_at,
                "data": data,
                "id": id,
                "isSaved": is_saved,
                "memoryAt": memory_at,
                "ownerId": owner_id,
                "type": type_,
                "updatedAt": updated_at,
            }
        )
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at
        if hide_at is not UNSET:
            field_dict["hideAt"] = hide_at
        if seen_at is not UNSET:
            field_dict["seenAt"] = seen_at
        if show_at is not UNSET:
            field_dict["showAt"] = show_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.asset_response_dto import AssetResponseDto
        from ..models.on_this_day_dto import OnThisDayDto

        d = dict(src_dict)
        assets = []
        _assets = d.pop("assets")
        for assets_item_data in _assets:
            assets_item = AssetResponseDto.from_dict(assets_item_data)

            assets.append(assets_item)

        created_at = isoparse(d.pop("createdAt"))

        data = OnThisDayDto.from_dict(d.pop("data"))

        id = d.pop("id")

        is_saved = d.pop("isSaved")

        memory_at = isoparse(d.pop("memoryAt"))

        owner_id = d.pop("ownerId")

        type_ = MemoryType(d.pop("type"))

        updated_at = isoparse(d.pop("updatedAt"))

        _deleted_at = d.pop("deletedAt", UNSET)
        deleted_at: Union[Unset, datetime.datetime]
        if isinstance(_deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = isoparse(_deleted_at)

        _hide_at = d.pop("hideAt", UNSET)
        hide_at: Union[Unset, datetime.datetime]
        if isinstance(_hide_at, Unset):
            hide_at = UNSET
        else:
            hide_at = isoparse(_hide_at)

        _seen_at = d.pop("seenAt", UNSET)
        seen_at: Union[Unset, datetime.datetime]
        if isinstance(_seen_at, Unset):
            seen_at = UNSET
        else:
            seen_at = isoparse(_seen_at)

        _show_at = d.pop("showAt", UNSET)
        show_at: Union[Unset, datetime.datetime]
        if isinstance(_show_at, Unset):
            show_at = UNSET
        else:
            show_at = isoparse(_show_at)

        memory_response_dto = cls(
            assets=assets,
            created_at=created_at,
            data=data,
            id=id,
            is_saved=is_saved,
            memory_at=memory_at,
            owner_id=owner_id,
            type_=type_,
            updated_at=updated_at,
            deleted_at=deleted_at,
            hide_at=hide_at,
            seen_at=seen_at,
            show_at=show_at,
        )

        memory_response_dto.additional_properties = d
        return memory_response_dto

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
