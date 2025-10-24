from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
    Union,
)
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.policy_condition_operator import PolicyConditionOperator
from ..models.policy_condition_subject import PolicyConditionSubject
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.policy import Policy


T = TypeVar("T", bound="PolicyCondition")


@_attrs_define
class PolicyCondition:
    """
    Attributes:
        operator (PolicyConditionOperator):
        subject (PolicyConditionSubject):
        value (str):
        uuid (UUID):
        policy (Union[Unset, Policy]):
    """

    operator: PolicyConditionOperator
    subject: PolicyConditionSubject
    value: str
    uuid: UUID
    policy: Union[Unset, "Policy"] = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        operator = self.operator.value

        subject = self.subject.value

        value = self.value

        uuid = str(self.uuid)

        policy: Union[Unset, dict[str, Any]] = UNSET
        if not isinstance(self.policy, Unset):
            policy = self.policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "operator": operator,
                "subject": subject,
                "value": value,
                "uuid": uuid,
            }
        )
        if policy is not UNSET:
            field_dict["policy"] = policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.policy import Policy

        d = dict(src_dict)
        operator = PolicyConditionOperator(d.pop("operator"))

        subject = PolicyConditionSubject(d.pop("subject"))

        value = d.pop("value")

        uuid = UUID(d.pop("uuid"))

        _policy = d.pop("policy", UNSET)
        policy: Union[Unset, Policy]
        if isinstance(_policy, Unset):
            policy = UNSET
        else:
            policy = Policy.from_dict(_policy)

        policy_condition = cls(
            operator=operator,
            subject=subject,
            value=value,
            uuid=uuid,
            policy=policy,
        )

        policy_condition.additional_properties = d
        return policy_condition

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
