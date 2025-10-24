from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="VexSubmitRequest")


@_attrs_define
class VexSubmitRequest:
    """
    Attributes:
        project (str):
        project_name (str):
        project_version (str):
        vex (str):
    """

    project: str
    project_name: str
    project_version: str
    vex: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        project = self.project

        project_name = self.project_name

        project_version = self.project_version

        vex = self.vex

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "project": project,
                "projectName": project_name,
                "projectVersion": project_version,
                "vex": vex,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        project = d.pop("project")

        project_name = d.pop("projectName")

        project_version = d.pop("projectVersion")

        vex = d.pop("vex")

        vex_submit_request = cls(
            project=project,
            project_name=project_name,
            project_version=project_version,
            vex=vex,
        )

        vex_submit_request.additional_properties = d
        return vex_submit_request

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
