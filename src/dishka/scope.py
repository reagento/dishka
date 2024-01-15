from enum import Enum
from functools import total_ordering


@total_ordering
class Scope(Enum):
    def __lt__(self, other) -> bool:
        if other is None:
            return False

        items = list(type(self))
        return items.index(self) < items.index(other)

    def next(self):
        items = list(type(self))
        return items[items.index(self) + 1]
