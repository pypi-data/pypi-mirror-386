from typing import Any, Dict, List, Type, TypeVar, Union

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="TimesheetLineCommentsModel")


@_attrs_define
class TimesheetLineCommentsModel:
    """
    Attributes:
        id (Union[Unset, int]):
        comments (Union[Unset, str]):
        hidden_comments (Union[Unset, str]):
    """

    id: Union[Unset, int] = UNSET
    comments: Union[Unset, str] = UNSET
    hidden_comments: Union[Unset, str] = UNSET
    additional_properties: Dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        id = self.id

        comments = self.comments

        hidden_comments = self.hidden_comments

        field_dict: Dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if comments is not UNSET:
            field_dict["comments"] = comments
        if hidden_comments is not UNSET:
            field_dict["hiddenComments"] = hidden_comments

        return field_dict

    @classmethod
    def from_dict(cls: Type[T], src_dict: Dict[str, Any]) -> T:
        d = src_dict.copy()
        id = d.pop("id", UNSET)

        comments = d.pop("comments", UNSET)

        hidden_comments = d.pop("hiddenComments", UNSET)

        timesheet_line_comments_model = cls(
            id=id,
            comments=comments,
            hidden_comments=hidden_comments,
        )

        timesheet_line_comments_model.additional_properties = d
        return timesheet_line_comments_model

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
