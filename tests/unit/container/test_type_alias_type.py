import sys
from typing import Any

import pytest

from dishka import (
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
    Integer,
    ListFloat,
    WrappedInteger,
    WrappedIntegerDep,
)


class MainProvider(Provider):
    scope = Scope.APP

    @provide
    def get_integer(self) -> Integer:
        return 1

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

HINT_VALUES =[
    (int, 1),
    (float, 1),
    (complex, 1),
    (list[float], [1.1, 1.2]),
    (WrappedInteger, 1),
]

@pytest.mark.parametrize(("hint", "value"), HINT_VALUES)
def test_type_alias_type(hint: Any, value: Any):
    container = make_container(MainProvider())
    assert container.get(hint) == value


@pytest.mark.parametrize(("hint", "value"), HINT_VALUES)
@pytest.mark.asyncio
async def test_type_alias_type_async(hint: Any, value: Any):
    container = make_async_container(MainProvider())
    assert await container.get(hint) == value
