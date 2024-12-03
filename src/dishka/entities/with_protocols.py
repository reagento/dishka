__all__ = ["WithProtocols"]

from typing import TYPE_CHECKING, TypeVar

from dishka._adaptix.common import TypeHint
from dishka._adaptix.type_tools import is_protocol, strip_alias
from dishka.entities.provides_marker import ProvideMultiple
from dishka.entities.with_parents import ParentsResolver
from dishka.text_rendering import get_name


def get_parents_protocols(type_hint: TypeHint) -> list[TypeHint]:
    parents = ParentsResolver().get_parents(type_hint)
    new_parents = [
        parent for parent in parents
        if is_protocol(strip_alias(parent))
    ]
    if new_parents:
        return new_parents

    name = get_name(type_hint, include_module=False)
    error_msg = (
        f"Not a single parent of the protocol was found in {name}.\n"
        "Hint:\n"
        f" * Maybe you meant just {name}, not WithProtocols[{name}]\n"
    )
    if len(parents) > 1:
        error_msg += f" * Perhaps you meant WithParents[{name}]?"
    raise ValueError(error_msg)


T = TypeVar("T")
if TYPE_CHECKING:
    from typing import Union
    WithProtocols = Union[T, T]  # noqa: UP007,PYI016
else:
    class WithProtocols:
        def __class_getitem__(cls, item: TypeHint) -> TypeHint:
            parents = get_parents_protocols(item)
            if len(parents) > 1:
                return ProvideMultiple(parents)
            return parents[0]
