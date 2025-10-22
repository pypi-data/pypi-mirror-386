from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="RosterShiftRole")


@_attrs_define
class RosterShiftRole:
    """
    Attributes:
        id (Union[Unset, int]):
        name (Union[Unset, str]):
        class_name (Union[Unset, str]):
        hex_colour_code (Union[Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    name: Union[Unset, str] = UNSET
    class_name: Union[Unset, str] = UNSET
    hex_colour_code: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        name = self.name

        class_name = self.class_name

        hex_colour_code = self.hex_colour_code

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if class_name is not UNSET:
            field_dict["className"] = class_name
        if hex_colour_code is not UNSET:
            field_dict["hexColourCode"] = hex_colour_code

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        class_name = d.pop("className", UNSET)

        hex_colour_code = d.pop("hexColourCode", UNSET)

        roster_shift_role = cls(
            id=id,
            name=name,
            class_name=class_name,
            hex_colour_code=hex_colour_code,
        )

        roster_shift_role.additional_properties = d
        return roster_shift_role

    @property
    def additional_keys(self) -> List[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
