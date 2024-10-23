from __future__ import annotations

import sys
import threading
from typing import TYPE_CHECKING, Generic, TypeVar

__all__ = ["AnyOf", "ProvideMultiple"]


if sys.version_info >= (3, 11):
    from typing import TypeVarTuple, Unpack

    Variants = TypeVarTuple("Variants")
    class ProvideMultiple(Generic[Unpack[Variants]]):
        pass
else:
    Variants = TypeVar("Variants")
    provides_lock = threading.Lock()

    class ProvideMultiple(Generic[Variants]):
        def __class_getitem__(cls, item):
            with provides_lock:
                cls.__parameters__ = [Variants]*len(item)
                return super().__class_getitem__(item)


if TYPE_CHECKING:
    from typing import Union as AnyOf
else:
    AnyOf = ProvideMultiple
