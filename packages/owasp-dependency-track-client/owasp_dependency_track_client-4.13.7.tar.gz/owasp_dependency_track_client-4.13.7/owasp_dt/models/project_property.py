from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
    Union,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.project_property_property_type import ProjectPropertyPropertyType
from ..types import UNSET, Unset

T = TypeVar("T", bound="ProjectProperty")


@_attrs_define
class ProjectProperty:
    """
    Attributes:
        group_name (str):
        property_name (str):
        property_type (ProjectPropertyPropertyType):
        property_value (Union[Unset, str]):
        description (Union[Unset, str]):
    """

    group_name: str
    property_name: str
    property_type: ProjectPropertyPropertyType
    property_value: Union[Unset, str] = UNSET
    description: Union[Unset, str] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        group_name = self.group_name

        property_name = self.property_name

        property_type = self.property_type.value

        property_value = self.property_value

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "groupName": group_name,
                "propertyName": property_name,
                "propertyType": property_type,
            }
        )
        if property_value is not UNSET:
            field_dict["propertyValue"] = property_value
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        group_name = d.pop("groupName")

        property_name = d.pop("propertyName")

        property_type = ProjectPropertyPropertyType(d.pop("propertyType"))

        property_value = d.pop("propertyValue", UNSET)

        description = d.pop("description", UNSET)

        project_property = cls(
            group_name=group_name,
            property_name=property_name,
            property_type=property_type,
            property_value=property_value,
            description=description,
        )

        project_property.additional_properties = d
        return project_property

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
