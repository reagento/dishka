from typing import Protocol


class Base[T](Protocol):
    value: T


class ImplBase[T](Base[T]):
    def __init__(self, value: T) -> None:
        self._value = value

    @property
    def value(self) -> T:
        return self._value
