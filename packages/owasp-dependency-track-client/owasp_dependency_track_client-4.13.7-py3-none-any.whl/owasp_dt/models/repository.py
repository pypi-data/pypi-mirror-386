from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.repository_type import RepositoryType
from ..types import UNSET, Unset

T = TypeVar("T", bound="Repository")


@_attrs_define
class Repository:
    """
    Attributes:
        type_ (RepositoryType):
        identifier (str):
        url (str):
        resolution_order (int):
        enabled (bool):
        internal (bool):
        uuid (UUID):
        authentication_required (Union[Unset, bool]):
        username (Union[Unset, str]):
        password (Union[Unset, str]):
    """

    type_: RepositoryType
    identifier: str
    url: str
    resolution_order: int
    enabled: bool
    internal: bool
    uuid: UUID
    authentication_required: Union[Unset, bool] = UNSET
    username: Union[Unset, str] = UNSET
    password: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_ = self.type_.value

        identifier = self.identifier

        url = self.url

        resolution_order = self.resolution_order

        enabled = self.enabled

        internal = self.internal

        uuid = str(self.uuid)

        authentication_required = self.authentication_required

        username = self.username

        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "type": type_,
                "identifier": identifier,
                "url": url,
                "resolutionOrder": resolution_order,
                "enabled": enabled,
                "internal": internal,
                "uuid": uuid,
            }
        )
        if authentication_required is not UNSET:
            field_dict["authenticationRequired"] = authentication_required
        if username is not UNSET:
            field_dict["username"] = username
        if password is not UNSET:
            field_dict["password"] = password

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        type_ = RepositoryType(d.pop("type"))

        identifier = d.pop("identifier")

        url = d.pop("url")

        resolution_order = d.pop("resolutionOrder")

        enabled = d.pop("enabled")

        internal = d.pop("internal")

        uuid = UUID(d.pop("uuid"))

        authentication_required = d.pop("authenticationRequired", UNSET)

        username = d.pop("username", UNSET)

        password = d.pop("password", UNSET)

        repository = cls(
            type_=type_,
            identifier=identifier,
            url=url,
            resolution_order=resolution_order,
            enabled=enabled,
            internal=internal,
            uuid=uuid,
            authentication_required=authentication_required,
            username=username,
            password=password,
        )

        repository.additional_properties = d
        return repository

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
