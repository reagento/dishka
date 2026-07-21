import inspect
import sys
from enum import Enum
from typing import TYPE_CHECKING, Annotated, ForwardRef, TypeVar


def _get_caller_module(stack_offset: int):
    frame = inspect.currentframe()
    if frame is None:
        raise RuntimeError("This python implementation does not support inspect.currentframe()")

    for _ in range(stack_offset):
        frame = frame.f_back
        if frame is None:
            raise RuntimeError("Unexpected end of call stack")
    return sys.modules[frame.f_globals["__name__"]]


class FwdRefMarker(Enum):
    VALUE = "VALUE"


if TYPE_CHECKING:
    T = TypeVar("T")
    FwdRef = Annotated[T, FwdRefMarker.VALUE]
else:
    class FwdRef:
        def __class_getitem__(cls, item):
            return Annotated[ForwardRef(item, module=_get_caller_module(2)), FwdRefMarker.VALUE]
