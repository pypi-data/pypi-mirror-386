from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.get_projects_response_200_item_client import GetProjectsResponse200ItemClient


T = TypeVar("T", bound="GetProjectsResponse200Item")


@_attrs_define
class GetProjectsResponse200Item:
    """
    Attributes:
        id (UUID):
        name (str):
        client_id (UUID):
        etag (str):
        created_at (Any):
        updated_at (Any):
        disabled (bool):
        client (GetProjectsResponse200ItemClient):
        api_key (str):
    """

    id: UUID
    name: str
    client_id: UUID
    etag: str
    created_at: Any
    updated_at: Any
    disabled: bool
    client: "GetProjectsResponse200ItemClient"
    api_key: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = str(self.id)

        name = self.name

        client_id = str(self.client_id)

        etag = self.etag

        created_at = self.created_at

        updated_at = self.updated_at

        disabled = self.disabled

        client = self.client.to_dict()

        api_key = self.api_key

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "name": name,
                "clientId": client_id,
                "etag": etag,
                "createdAt": created_at,
                "updatedAt": updated_at,
                "disabled": disabled,
                "client": client,
                "apiKey": api_key,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.get_projects_response_200_item_client import GetProjectsResponse200ItemClient

        d = dict(src_dict)
        id = UUID(d.pop("id"))

        name = d.pop("name")

        client_id = UUID(d.pop("clientId"))

        etag = d.pop("etag")

        created_at = d.pop("createdAt")

        updated_at = d.pop("updatedAt")

        disabled = d.pop("disabled")

        client = GetProjectsResponse200ItemClient.from_dict(d.pop("client"))

        api_key = d.pop("apiKey")

        get_projects_response_200_item = cls(
            id=id,
            name=name,
            client_id=client_id,
            etag=etag,
            created_at=created_at,
            updated_at=updated_at,
            disabled=disabled,
            client=client,
            api_key=api_key,
        )

        get_projects_response_200_item.additional_properties = d
        return get_projects_response_200_item

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
