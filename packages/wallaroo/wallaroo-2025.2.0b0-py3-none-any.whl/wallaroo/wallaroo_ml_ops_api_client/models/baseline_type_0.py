from collections.abc import Mapping
from typing import (
    TYPE_CHECKING,
    Any,
    TypeVar,
)

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

if TYPE_CHECKING:
    from ..models.field_tagged_summaries import FieldTaggedSummaries


T = TypeVar("T", bound="BaselineType0")


@_attrs_define
class BaselineType0:
    """
    Attributes:
        summary (FieldTaggedSummaries): This allows us to compute multiple [SeriesSummary]ies and score them in bulk.
    """

    summary: "FieldTaggedSummaries"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        summary = self.summary.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "Summary": summary,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.field_tagged_summaries import FieldTaggedSummaries

        d = dict(src_dict)
        summary = FieldTaggedSummaries.from_dict(d.pop("Summary"))

        baseline_type_0 = cls(
            summary=summary,
        )

        baseline_type_0.additional_properties = d
        return baseline_type_0

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
