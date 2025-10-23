from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ReportingDimensionValueFilterApiModel")


@_attrs_define
class ReportingDimensionValueFilterApiModel:
    """
    Attributes:
        filter_type (Union[Unset, str]):
        value (Union[Unset, str]):
    """

    filter_type: Union[Unset, str] = UNSET
    value: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        filter_type = self.filter_type

        value = self.value

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if filter_type is not UNSET:
            field_dict["filterType"] = filter_type
        if value is not UNSET:
            field_dict["value"] = value

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        filter_type = d.pop("filterType", UNSET)

        value = d.pop("value", UNSET)

        reporting_dimension_value_filter_api_model = cls(
            filter_type=filter_type,
            value=value,
        )

        reporting_dimension_value_filter_api_model.additional_properties = d
        return reporting_dimension_value_filter_api_model

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
