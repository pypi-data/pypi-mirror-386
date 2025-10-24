from __future__ import annotations
from typing import Literal, Optional, Union
from instaui.components.element import Element
from instaui.vars.types import TMaybeRef
from instaui.components._responsive_type._common import (
    TMaybeResponsive,
    TLevel_1_9,
)
from instaui.components._responsive_type._typography import (
    TWeightEnum,
    TTextWrapEnum,
    TTrimEnum,
    TAlignEnum,
)


class Label(Element):
    def __init__(
        self,
        text: Optional[TMaybeRef[str]] = None,
        *,
        label_side: Optional[TMaybeRef[Union[Literal["left", "right"], str]]] = None,
        size: Optional[TMaybeResponsive[Union[TLevel_1_9, str]]] = None,
        weight: Optional[TMaybeResponsive[Union[TWeightEnum, str]]] = None,
        align: Optional[TMaybeResponsive[Union[TAlignEnum, str]]] = None,
        trim: Optional[TMaybeRef[Union[TTrimEnum, str]]] = None,
        truncate: Optional[TMaybeRef[bool]] = None,
        text_wrap: Optional[TMaybeRef[Union[TTextWrapEnum, str]]] = None,
    ):
        super().__init__("ui_label")

        self.props(
            {
                "label_side": label_side,
                "text": text,
                "size": size,
                "weight": weight,
                "text_align": align,
                "trim": trim,
                "truncate": truncate,
                "text_wrap": text_wrap,
            }
        )
