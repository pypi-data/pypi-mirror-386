from collections.abc import Mapping
from typing import (
    Any,
    TypeVar,
)
from uuid import UUID

from attrs import (
    define as _attrs_define,
    field as _attrs_field,
)

T = TypeVar("T", bound="GetTasksByOrchShaResponse")


@_attrs_define
class GetTasksByOrchShaResponse:
    """
    Attributes:
        ids (list[UUID]):
    """

    ids: list[UUID]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ids = []
        for ids_item_data in self.ids:
            ids_item = str(ids_item_data)
            ids.append(ids_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "ids": ids,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ids = []
        _ids = d.pop("ids")
        for ids_item_data in _ids:
            ids_item = UUID(ids_item_data)

            ids.append(ids_item)

        get_tasks_by_orch_sha_response = cls(
            ids=ids,
        )

        get_tasks_by_orch_sha_response.additional_properties = d
        return get_tasks_by_orch_sha_response

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
