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
    from ..models.resources import Resources


T = TypeVar("T", bound="SidekickConfigImagesType0")


@_attrs_define
class SidekickConfigImagesType0:
    """ """

    additional_properties: dict[str, "Resources"] = _attrs_field(
        init=False, factory=dict
    )

    def to_dict(self) -> dict[str, Any]:
        field_dict: dict[str, Any] = {}
        for prop_name, prop in self.additional_properties.items():
            field_dict[prop_name] = prop.to_dict()

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.resources import Resources

        d = dict(src_dict)
        sidekick_config_images_type_0 = cls()

        additional_properties = {}
        for prop_name, prop_dict in d.items():
            additional_property = Resources.from_dict(prop_dict)

            additional_properties[prop_name] = additional_property

        sidekick_config_images_type_0.additional_properties = additional_properties
        return sidekick_config_images_type_0

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> "Resources":
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: "Resources") -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
