from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostClientsResponse201")


@_attrs_define
class PostClientsResponse201:
    """
    Attributes:
        id (UUID):
        name (str):
        etag (str):
        created_at (Any):
        updated_at (Any):
        disabled (bool):
    """

    id: UUID
    name: str
    etag: str
    created_at: Any
    updated_at: Any
    disabled: bool
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        etag = self.etag

        created_at = self.created_at

        updated_at = self.updated_at

        disabled = self.disabled

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "etag": etag,
                "createdAt": created_at,
                "updatedAt": updated_at,
                "disabled": disabled,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        etag = d.pop("etag")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        disabled = d.pop("disabled")

        post_clients_response_201 = cls(
            id=id,
            name=name,
            etag=etag,
            created_at=created_at,
            updated_at=updated_at,
            disabled=disabled,
        )

        post_clients_response_201.additional_properties = d
        return post_clients_response_201

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
