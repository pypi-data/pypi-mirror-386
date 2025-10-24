from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Framework")


@_attrs_define
class Framework:
    """
    Attributes:
        name (Union[Unset, str]):
        version (Union[Unset, str]):
        timestamp (Union[Unset, str]):
        uuid (Union[Unset, str]):
    """

    name: Union[Unset, str] = UNSET
    version: Union[Unset, str] = UNSET
    timestamp: Union[Unset, str] = UNSET
    uuid: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        version = self.version

        timestamp = self.timestamp

        uuid = self.uuid

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if version is not UNSET:
            field_dict["version"] = version
        if timestamp is not UNSET:
            field_dict["timestamp"] = timestamp
        if uuid is not UNSET:
            field_dict["uuid"] = uuid

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        version = d.pop("version", UNSET)

        timestamp = d.pop("timestamp", UNSET)

        uuid = d.pop("uuid", UNSET)

        framework = cls(
            name=name,
            version=version,
            timestamp=timestamp,
            uuid=uuid,
        )

        framework.additional_properties = d
        return framework

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
