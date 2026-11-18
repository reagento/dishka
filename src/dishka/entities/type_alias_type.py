import sys
from typing import Any

from dishka._adaptix.common import TypeHint

if sys.version_info >= (3, 12):
    from typing import TypeAliasType

    def is_type_alias_type(tp: TypeHint) -> bool:
        return isinstance(tp, TypeAliasType)

else:
    def is_type_alias_type(tp: TypeHint) -> bool:
        return False


def unwrap_type_alias(hint: Any) -> Any:
    seen: set[Any] = set()
    while is_type_alias_type(hint):
        if hint in seen:
            break
        seen.add(hint)
        hint = hint.__value__
    return hint
