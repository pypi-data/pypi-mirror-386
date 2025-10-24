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
    from ..models.multivariate_continuous import MultivariateContinuous


T = TypeVar("T", bound="SummarizerType1")


@_attrs_define
class SummarizerType1:
    """
    Attributes:
        multivariate_continuous (MultivariateContinuous):
    """

    multivariate_continuous: "MultivariateContinuous"
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        multivariate_continuous = self.multivariate_continuous.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "MultivariateContinuous": multivariate_continuous,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.multivariate_continuous import MultivariateContinuous

        d = dict(src_dict)
        multivariate_continuous = MultivariateContinuous.from_dict(
            d.pop("MultivariateContinuous")
        )

        summarizer_type_1 = cls(
            multivariate_continuous=multivariate_continuous,
        )

        summarizer_type_1.additional_properties = d
        return summarizer_type_1

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
