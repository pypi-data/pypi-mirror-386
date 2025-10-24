from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="PostTracesBody")


@_attrs_define
class PostTracesBody:
    """
    Attributes:
        user_id (str):
        session_id (str):
        model (str):
        token (float):
        content (str):
        started_at (str):
        ended_at (str):
    """

    user_id: str
    session_id: str
    model: str
    token: float
    content: str
    started_at: str
    ended_at: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        user_id = self.user_id

        session_id = self.session_id

        model = self.model

        token = self.token

        content = self.content

        started_at = self.started_at

        ended_at = self.ended_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "userId": user_id,
                "sessionId": session_id,
                "model": model,
                "token": token,
                "content": content,
                "startedAt": started_at,
                "endedAt": ended_at,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        user_id = d.pop("userId")

        session_id = d.pop("sessionId")

        model = d.pop("model")

        token = d.pop("token")

        content = d.pop("content")

        started_at = d.pop("startedAt")

        ended_at = d.pop("endedAt")

        post_traces_body = cls(
            user_id=user_id,
            session_id=session_id,
            model=model,
            token=token,
            content=content,
            started_at=started_at,
            ended_at=ended_at,
        )

        post_traces_body.additional_properties = d
        return post_traces_body

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
