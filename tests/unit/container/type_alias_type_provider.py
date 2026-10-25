from collections.abc import Iterable
from typing import Annotated

from dishka import FromComponent

type Integer = int
type Integer2 = int
type String = str
type ListFloat = list[float]
type WrappedIntegerDep = Integer
type IntegerWithComponent = Annotated[int, FromComponent("X")]
type IterableInt = Iterable[Integer]
type IntStr = Integer | String
type BytesMemoryView = bytes | memoryview
type StrNone = String | None


class Service:
    pass


type ServiceAlias = Service
type WrappedServiceAlias = ServiceAlias


class Consumer:
    def __init__(self, service: ServiceAlias) -> None:
        self.service = service
