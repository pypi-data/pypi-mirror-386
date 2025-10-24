from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateOidcAccessTokenBody")


@_attrs_define
class ValidateOidcAccessTokenBody:
    """
    Attributes:
        id_token (str): An OAuth2 access token
        access_token (Union[Unset, str]):
    """

    id_token: str
    access_token: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id_token = self.id_token

        access_token = self.access_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "idToken": id_token,
            }
        )
        if access_token is not UNSET:
            field_dict["accessToken"] = access_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id_token = d.pop("idToken")

        access_token = d.pop("accessToken", UNSET)

        validate_oidc_access_token_body = cls(
            id_token=id_token,
            access_token=access_token,
        )

        validate_oidc_access_token_body.additional_properties = d
        return validate_oidc_access_token_body

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
