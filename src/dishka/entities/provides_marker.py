from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Union as AnyOF
else:
    class AnyOf:
        def __class_getitem__(cls, item):
            if isinstance(item, tuple):
                return ProvideMultiple(item)
            return item


class ProvideMultiple:
    def __init__(self, items):
        self.items = items
