from typing import Protocol


class D[T](Protocol):
    dep: T


class A[T](D[T]):
    def __init__(self, dep: T) -> None:
        self._dep = dep

    @property
    def dep(self) -> T:
        return self._dep


class Base[T, U](Protocol):
    first: T
    second: U


class Impl[T, U](Base[T, U]):
    def __init__(self, first: T, second: U) -> None:
        self._first = first
        self._second = second

    @property
    def first(self) -> T:
        return self._first

    @property
    def second(self) -> U:
        return self._second


class Outer[T](Protocol):
    value: T


class Inner[T](Protocol):
    data: T


class InnerImpl[T](Inner[T]):
    def __init__(self, data: T) -> None:
        self._data = data

    @property
    def data(self) -> T:
        return self._data


class Wrapper[T](Outer[Inner[T]]):
    def __init__(self, inner: Inner[T]) -> None:
        self._value = inner

    @property
    def value(self) -> Inner[T]:
        return self._value


class Base1[T](Protocol):
    value1: T


class Base2[U](Protocol):
    value2: U


class Combined[T, U](Base1[T], Base2[U]):
    def __init__(self, value1: T, value2: U) -> None:
        self._value1 = value1
        self._value2 = value2

    @property
    def value1(self) -> T:
        return self._value1

    @property
    def value2(self) -> U:
        return self._value2
