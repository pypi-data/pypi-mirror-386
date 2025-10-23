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
    from ..models.albums_update import AlbumsUpdate
    from ..models.avatar_update import AvatarUpdate
    from ..models.cast_update import CastUpdate
    from ..models.download_update import DownloadUpdate
    from ..models.email_notifications_update import EmailNotificationsUpdate
    from ..models.folders_update import FoldersUpdate
    from ..models.memories_update import MemoriesUpdate
    from ..models.people_update import PeopleUpdate
    from ..models.purchase_update import PurchaseUpdate
    from ..models.ratings_update import RatingsUpdate
    from ..models.shared_links_update import SharedLinksUpdate
    from ..models.tags_update import TagsUpdate


T = TypeVar("T", bound="UserPreferencesUpdateDto")


@_attrs_define
class UserPreferencesUpdateDto:
    """
    Attributes:
        albums (Union[Unset, AlbumsUpdate]):
        avatar (Union[Unset, AvatarUpdate]):
        cast (Union[Unset, CastUpdate]):
        download (Union[Unset, DownloadUpdate]):
        email_notifications (Union[Unset, EmailNotificationsUpdate]):
        folders (Union[Unset, FoldersUpdate]):
        memories (Union[Unset, MemoriesUpdate]):
        people (Union[Unset, PeopleUpdate]):
        purchase (Union[Unset, PurchaseUpdate]):
        ratings (Union[Unset, RatingsUpdate]):
        shared_links (Union[Unset, SharedLinksUpdate]):
        tags (Union[Unset, TagsUpdate]):
    """

    albums: Union[Unset, "AlbumsUpdate"] = UNSET
    avatar: Union[Unset, "AvatarUpdate"] = UNSET
    cast: Union[Unset, "CastUpdate"] = UNSET
    download: Union[Unset, "DownloadUpdate"] = UNSET
    email_notifications: Union[Unset, "EmailNotificationsUpdate"] = UNSET
    folders: Union[Unset, "FoldersUpdate"] = UNSET
    memories: Union[Unset, "MemoriesUpdate"] = UNSET
    people: Union[Unset, "PeopleUpdate"] = UNSET
    purchase: Union[Unset, "PurchaseUpdate"] = UNSET
    ratings: Union[Unset, "RatingsUpdate"] = UNSET
    shared_links: Union[Unset, "SharedLinksUpdate"] = UNSET
    tags: Union[Unset, "TagsUpdate"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        albums: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.albums, Unset):
            albums = self.albums.to_dict()

        avatar: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.avatar, Unset):
            avatar = self.avatar.to_dict()

        cast: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.cast, Unset):
            cast = self.cast.to_dict()

        download: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.download, Unset):
            download = self.download.to_dict()

        email_notifications: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.email_notifications, Unset):
            email_notifications = self.email_notifications.to_dict()

        folders: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.folders, Unset):
            folders = self.folders.to_dict()

        memories: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.memories, Unset):
            memories = self.memories.to_dict()

        people: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.people, Unset):
            people = self.people.to_dict()

        purchase: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.purchase, Unset):
            purchase = self.purchase.to_dict()

        ratings: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.ratings, Unset):
            ratings = self.ratings.to_dict()

        shared_links: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.shared_links, Unset):
            shared_links = self.shared_links.to_dict()

        tags: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.tags, Unset):
            tags = self.tags.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if albums is not UNSET:
            field_dict["albums"] = albums
        if avatar is not UNSET:
            field_dict["avatar"] = avatar
        if cast is not UNSET:
            field_dict["cast"] = cast
        if download is not UNSET:
            field_dict["download"] = download
        if email_notifications is not UNSET:
            field_dict["emailNotifications"] = email_notifications
        if folders is not UNSET:
            field_dict["folders"] = folders
        if memories is not UNSET:
            field_dict["memories"] = memories
        if people is not UNSET:
            field_dict["people"] = people
        if purchase is not UNSET:
            field_dict["purchase"] = purchase
        if ratings is not UNSET:
            field_dict["ratings"] = ratings
        if shared_links is not UNSET:
            field_dict["sharedLinks"] = shared_links
        if tags is not UNSET:
            field_dict["tags"] = tags

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.albums_update import AlbumsUpdate
        from ..models.avatar_update import AvatarUpdate
        from ..models.cast_update import CastUpdate
        from ..models.download_update import DownloadUpdate
        from ..models.email_notifications_update import EmailNotificationsUpdate
        from ..models.folders_update import FoldersUpdate
        from ..models.memories_update import MemoriesUpdate
        from ..models.people_update import PeopleUpdate
        from ..models.purchase_update import PurchaseUpdate
        from ..models.ratings_update import RatingsUpdate
        from ..models.shared_links_update import SharedLinksUpdate
        from ..models.tags_update import TagsUpdate

        d = dict(src_dict)
        _albums = d.pop("albums", UNSET)
        albums: Union[Unset, AlbumsUpdate]
        if isinstance(_albums, Unset):
            albums = UNSET
        else:
            albums = AlbumsUpdate.from_dict(_albums)

        _avatar = d.pop("avatar", UNSET)
        avatar: Union[Unset, AvatarUpdate]
        if isinstance(_avatar, Unset):
            avatar = UNSET
        else:
            avatar = AvatarUpdate.from_dict(_avatar)

        _cast = d.pop("cast", UNSET)
        cast: Union[Unset, CastUpdate]
        if isinstance(_cast, Unset):
            cast = UNSET
        else:
            cast = CastUpdate.from_dict(_cast)

        _download = d.pop("download", UNSET)
        download: Union[Unset, DownloadUpdate]
        if isinstance(_download, Unset):
            download = UNSET
        else:
            download = DownloadUpdate.from_dict(_download)

        _email_notifications = d.pop("emailNotifications", UNSET)
        email_notifications: Union[Unset, EmailNotificationsUpdate]
        if isinstance(_email_notifications, Unset):
            email_notifications = UNSET
        else:
            email_notifications = EmailNotificationsUpdate.from_dict(
                _email_notifications
            )

        _folders = d.pop("folders", UNSET)
        folders: Union[Unset, FoldersUpdate]
        if isinstance(_folders, Unset):
            folders = UNSET
        else:
            folders = FoldersUpdate.from_dict(_folders)

        _memories = d.pop("memories", UNSET)
        memories: Union[Unset, MemoriesUpdate]
        if isinstance(_memories, Unset):
            memories = UNSET
        else:
            memories = MemoriesUpdate.from_dict(_memories)

        _people = d.pop("people", UNSET)
        people: Union[Unset, PeopleUpdate]
        if isinstance(_people, Unset):
            people = UNSET
        else:
            people = PeopleUpdate.from_dict(_people)

        _purchase = d.pop("purchase", UNSET)
        purchase: Union[Unset, PurchaseUpdate]
        if isinstance(_purchase, Unset):
            purchase = UNSET
        else:
            purchase = PurchaseUpdate.from_dict(_purchase)

        _ratings = d.pop("ratings", UNSET)
        ratings: Union[Unset, RatingsUpdate]
        if isinstance(_ratings, Unset):
            ratings = UNSET
        else:
            ratings = RatingsUpdate.from_dict(_ratings)

        _shared_links = d.pop("sharedLinks", UNSET)
        shared_links: Union[Unset, SharedLinksUpdate]
        if isinstance(_shared_links, Unset):
            shared_links = UNSET
        else:
            shared_links = SharedLinksUpdate.from_dict(_shared_links)

        _tags = d.pop("tags", UNSET)
        tags: Union[Unset, TagsUpdate]
        if isinstance(_tags, Unset):
            tags = UNSET
        else:
            tags = TagsUpdate.from_dict(_tags)

        user_preferences_update_dto = cls(
            albums=albums,
            avatar=avatar,
            cast=cast,
            download=download,
            email_notifications=email_notifications,
            folders=folders,
            memories=memories,
            people=people,
            purchase=purchase,
            ratings=ratings,
            shared_links=shared_links,
            tags=tags,
        )

        user_preferences_update_dto.additional_properties = d
        return user_preferences_update_dto

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
