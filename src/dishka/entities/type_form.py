import sys
from typing import TYPE_CHECKING, Any, Generic, TypeVar

if TYPE_CHECKING:   # ast-grep-ignore: DISHKA001
    if sys.version_info >= (3, 15):
        from typing import TypeForm
    else:
        T = TypeVar("T")
        class TypeForm(Generic[T]):
            pass
else:
    TypeForm = Any

