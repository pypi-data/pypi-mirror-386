from __future__ import annotations
import sys
from typing import _TypedDict, Generic, Literal, TypeVar, TypedDict, Union
from instaui.vars.types import TMaybeRef

TLevel_0_9 = Literal["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
TLevel_1_9 = Literal["1", "2", "3", "4", "5", "6", "7", "8", "9"]
TLevel_neg_9_9 = Literal[
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
    "-1",
    "-2",
    "-3",
    "-4",
    "-5",
    "-6",
    "-7",
    "-8",
    "-9",
]

TWithAutoValue = Literal["auto"]
_T_Value = TypeVar("_T_Value")

if sys.version_info >= (3, 11):

    class TResponsive(TypedDict, Generic[_T_Value], total=False):
        initial: TMaybeRef[_T_Value]
        xs: TMaybeRef[_T_Value]
        sm: TMaybeRef[_T_Value]
        md: TMaybeRef[_T_Value]
        lg: TMaybeRef[_T_Value]
        xl: TMaybeRef[_T_Value]

    TMaybeResponsive = Union[TResponsive[_T_Value], TMaybeRef[_T_Value]]
else:

    class TResponsive(_TypedDict, total=False):
        initial: TMaybeRef
        xs: TMaybeRef
        sm: TMaybeRef
        md: TMaybeRef
        lg: TMaybeRef
        xl: TMaybeRef

    TMaybeResponsive = Union[TResponsive, TMaybeRef[_T_Value]]
