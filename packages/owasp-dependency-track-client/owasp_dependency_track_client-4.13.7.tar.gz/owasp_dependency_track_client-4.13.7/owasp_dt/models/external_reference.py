from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.external_reference_type import ExternalReferenceType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ExternalReference")


@_attrs_define
class ExternalReference:
    """
    Attributes:
        url (str):
        type_ (Union[Unset, ExternalReferenceType]):
        comment (Union[Unset, str]):
    """

    url: str
    type_: Union[Unset, ExternalReferenceType] = UNSET
    comment: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        url = self.url

        type_: Union[Unset, str] = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        comment = self.comment

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "url": url,
            }
        )
        if type_ is not UNSET:
            field_dict["type"] = type_
        if comment is not UNSET:
            field_dict["comment"] = comment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        url = d.pop("url")

        _type_ = d.pop("type", UNSET)
        type_: Union[Unset, ExternalReferenceType]
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = ExternalReferenceType(_type_)

        comment = d.pop("comment", UNSET)

        external_reference = cls(
            url=url,
            type_=type_,
            comment=comment,
        )

        external_reference.additional_properties = d
        return external_reference

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
