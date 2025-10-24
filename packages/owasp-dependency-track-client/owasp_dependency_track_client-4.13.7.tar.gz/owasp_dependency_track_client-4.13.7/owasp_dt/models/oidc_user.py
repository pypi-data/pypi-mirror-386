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
    from ..models.permission import Permission
    from ..models.team import Team


T = TypeVar("T", bound="OidcUser")


@_attrs_define
class OidcUser:
    """
    Attributes:
        username (str):
        subject_identifier (Union[Unset, str]):
        email (Union[Unset, str]):
        teams (Union[Unset, list['Team']]):
        permissions (Union[Unset, list['Permission']]):
    """

    username: str
    subject_identifier: Union[Unset, str] = UNSET
    email: Union[Unset, str] = UNSET
    teams: Union[Unset, list["Team"]] = UNSET
    permissions: Union[Unset, list["Permission"]] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        username = self.username

        subject_identifier = self.subject_identifier

        email = self.email

        teams: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.teams, Unset):
            teams = []
            for teams_item_data in self.teams:
                teams_item = teams_item_data.to_dict()
                teams.append(teams_item)

        permissions: Union[Unset, list[dict[str, Any]]] = UNSET
        if not isinstance(self.permissions, Unset):
            permissions = []
            for permissions_item_data in self.permissions:
                permissions_item = permissions_item_data.to_dict()
                permissions.append(permissions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "username": username,
            }
        )
        if subject_identifier is not UNSET:
            field_dict["subjectIdentifier"] = subject_identifier
        if email is not UNSET:
            field_dict["email"] = email
        if teams is not UNSET:
            field_dict["teams"] = teams
        if permissions is not UNSET:
            field_dict["permissions"] = permissions

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.permission import Permission
        from ..models.team import Team

        d = dict(src_dict)
        username = d.pop("username")

        subject_identifier = d.pop("subjectIdentifier", UNSET)

        email = d.pop("email", UNSET)

        teams = []
        _teams = d.pop("teams", UNSET)
        for teams_item_data in _teams or []:
            teams_item = Team.from_dict(teams_item_data)

            teams.append(teams_item)

        permissions = []
        _permissions = d.pop("permissions", UNSET)
        for permissions_item_data in _permissions or []:
            permissions_item = Permission.from_dict(permissions_item_data)

            permissions.append(permissions_item)

        oidc_user = cls(
            username=username,
            subject_identifier=subject_identifier,
            email=email,
            teams=teams,
            permissions=permissions,
        )

        oidc_user.additional_properties = d
        return oidc_user

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
