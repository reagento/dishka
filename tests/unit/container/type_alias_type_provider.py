from typing import Annotated

from dishka import FromComponent

type Integer = int
type Integer2 = int
type ListFloat = list[float]
type WrappedInteger = Integer
type WrappedIntegerDep = Integer
type IntegerWithComponent = Annotated[int, FromComponent("X")]
