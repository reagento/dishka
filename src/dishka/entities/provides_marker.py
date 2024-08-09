from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING, Any

__all__ = ["AnyOf", "ProvideMultiple"]

if TYPE_CHECKING:
    from typing import Union as AnyOf
else:
    class AnyOf:
        def __class_getitem__(cls, item: Any) -> Any:
            if isinstance(item, tuple):
                return ProvideMultiple(item)
            return item


class ProvideMultiple:
    def __init__(self, items: Sequence[Any]) -> None:
        self.items = items
