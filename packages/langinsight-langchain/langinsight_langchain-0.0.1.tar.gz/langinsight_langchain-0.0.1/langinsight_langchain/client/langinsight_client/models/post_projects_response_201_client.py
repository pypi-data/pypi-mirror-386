from collections.abc import Mapping
from typing import Any, TypeVar, Union, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PostProjectsResponse201Client")


@_attrs_define
class PostProjectsResponse201Client:
    """
    Attributes:
        etag (str):
        created_at (Any):
        updated_at (Any):
        id (UUID):
        name (str):
        deleted_at (Union[Any, None, Unset]):
    """

    etag: str
    created_at: Any
    updated_at: Any
    id: UUID
    name: str
    deleted_at: Union[Any, None, Unset] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        etag = self.etag

        created_at = self.created_at

        updated_at = self.updated_at

        id = str(self.id)

        name = self.name

        deleted_at: Union[Any, None, Unset]
        if isinstance(self.deleted_at, Unset):
            deleted_at = UNSET
        else:
            deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "etag": etag,
                "created_at": created_at,
                "updated_at": updated_at,
                "id": id,
                "name": name,
            }
        )
        if deleted_at is not UNSET:
            field_dict["deleted_at"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        etag = d.pop("etag")

        created_at = d.pop("created_at")

        updated_at = d.pop("updated_at")

        id = UUID(d.pop("id"))

        name = d.pop("name")

        def _parse_deleted_at(data: object) -> Union[Any, None, Unset]:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(Union[Any, None, Unset], data)

        deleted_at = _parse_deleted_at(d.pop("deleted_at", UNSET))

        post_projects_response_201_client = cls(
            etag=etag,
            created_at=created_at,
            updated_at=updated_at,
            id=id,
            name=name,
            deleted_at=deleted_at,
        )

        post_projects_response_201_client.additional_properties = d
        return post_projects_response_201_client

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
