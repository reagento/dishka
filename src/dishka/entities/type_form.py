import sys
from typing import Generic, TypeVar

if sys.version_info >= (3, 15):
    from typing import TypeForm
else:
    T = TypeVar("T")
    class TypeForm(Generic[T]):
        pass
