from collections.abc import Iterable
from typing import Annotated

from dishka import FromComponent

type Integer = int
type Integer2 = int
type String = str
type ListFloat = list[float]
type WrappedInteger = Integer
type WrappedIntegerDep = Integer
type IntegerWithComponent = Annotated[int, FromComponent("X")]
type IterableInt = Iterable[Integer]
type IntStr = Integer | String
type BytesMemoryView = bytes | memoryview
