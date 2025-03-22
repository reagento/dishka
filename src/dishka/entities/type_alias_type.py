import sys

from dishka._adaptix.common import TypeHint

if sys.version_info >= (3, 12):
    from typing import TypeAliasType

    def is_type_alias_type(tp: TypeHint) -> bool:
        return isinstance(tp, TypeAliasType)

else:
    def is_type_alias_type(tp: TypeHint) -> bool:
        return False
