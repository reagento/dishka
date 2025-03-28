import sys
from typing import Any

import pytest

from dishka import (
    AnyOf,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)

if sys.version_info < (3, 12):
    pytest.skip(
        "Type alias is supported on Python 3.12+ only",
        allow_module_level=True,
    )

from .type_alias_type_provider import (
    BytesMemoryView,
    Integer,
    IntegerWithComponent,
    IntStr,
    IterableInt,
    ListFloat,
    WrappedInteger,
    WrappedIntegerDep,
)


class MainProvider(Provider):
    scope = Scope.APP

    @provide
    def get_iterable_int(self) -> IterableInt:
        yield 1

    @provide
    def get_list_float(self) -> ListFloat:
        return [1.1, 1.2]

    @provide
    def get_wrapped_integer(self) -> WrappedInteger:
        return 1

    @provide
    def get_float(self, dep: Integer) -> float:
        return dep

    @provide
    def get_complex(self, dep: WrappedIntegerDep) -> complex:
        return dep

    @provide
    def get_integer_string_union(self) -> IntStr:
        return "foo"

    @provide
    def get_bytes_memoryview_union(self) -> BytesMemoryView:
        return b"foo"

    @provide
    def get_bytes_memoryview(
        self, value: BytesMemoryView,
    ) -> AnyOf[bytes, memoryview]:
        return value + b"1"

HINT_VALUES = [
    (int, 1),
    (float, 1),
    (complex, 1),
    (list[float], [1.1, 1.2]),
    (WrappedInteger, 1),
    (IntStr, "foo"),
    (BytesMemoryView, b"foo"),
    (bytes, b"foo1"),
    (memoryview, b"foo1"),
]


@pytest.mark.parametrize(("hint", "value"), HINT_VALUES)
def test_type_alias(hint: Any, value: Any):
    container = make_container(MainProvider())
    assert container.get(hint) == value


@pytest.mark.parametrize(("hint", "value"), HINT_VALUES)
@pytest.mark.asyncio
async def test_type_alias_async(hint: Any, value: Any):
    container = make_async_container(MainProvider())
    assert await container.get(hint) == value


class ComponentProvider(Provider):
    scope = Scope.APP
    component = "X"

    @provide
    def get_int(self) -> int:
        return 42


class ComponentProviderAlt(Provider):
    scope = Scope.APP
    component = "X"

    @provide
    def get_int(self) -> IntegerWithComponent:
        return 42


class ComponentDepProvider(Provider):
    scope = Scope.APP

    @provide
    def get_str(self, dep: IntegerWithComponent) -> str:
        return str(dep)


COMPONENT_PRIVDER_VALUES = [
    ComponentProvider(),
    ComponentProviderAlt(),
]


@pytest.mark.parametrize("component_provider", COMPONENT_PRIVDER_VALUES)
def test_type_alias_component(component_provider):
    @component_provider.provide
    def foo() -> IntegerWithComponent:
        return 42

    container = make_container(
        ComponentDepProvider(),
        component_provider,
    )
    assert container.get(int, component="X") == 42
    assert container.get(str) == "42"


@pytest.mark.parametrize("component_provider", COMPONENT_PRIVDER_VALUES)
@pytest.mark.asyncio
async def test_type_alias_component_async(component_provider):
    container = make_async_container(
        ComponentDepProvider(),
        component_provider,
    )
    assert await container.get(int, component="X") == 42
    assert await container.get(str) == "42"
