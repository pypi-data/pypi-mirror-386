from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.create_scheduled_notification_rule_request_notification_level import (
    CreateScheduledNotificationRuleRequestNotificationLevel,
)
from ..models.create_scheduled_notification_rule_request_scope import (
    CreateScheduledNotificationRuleRequestScope,
)

if TYPE_CHECKING:
    from ..models.publisher import Publisher


T = TypeVar("T", bound="CreateScheduledNotificationRuleRequest")


@_attrs_define
class CreateScheduledNotificationRuleRequest:
    """
    Attributes:
        name (str):
        scope (CreateScheduledNotificationRuleRequestScope):
        notification_level (CreateScheduledNotificationRuleRequestNotificationLevel):
        publisher (Publisher):
    """

    name: str
    scope: CreateScheduledNotificationRuleRequestScope
    notification_level: CreateScheduledNotificationRuleRequestNotificationLevel
    publisher: "Publisher"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        scope = self.scope.value

        notification_level = self.notification_level.value

        publisher = self.publisher.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "scope": scope,
                "notificationLevel": notification_level,
                "publisher": publisher,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.publisher import Publisher

        d = dict(src_dict)
        name = d.pop("name")

        scope = CreateScheduledNotificationRuleRequestScope(d.pop("scope"))

        notification_level = CreateScheduledNotificationRuleRequestNotificationLevel(
            d.pop("notificationLevel")
        )

        publisher = Publisher.from_dict(d.pop("publisher"))

        create_scheduled_notification_rule_request = cls(
            name=name,
            scope=scope,
            notification_level=notification_level,
            publisher=publisher,
        )

        create_scheduled_notification_rule_request.additional_properties = d
        return create_scheduled_notification_rule_request

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
