import pytest

from dishka import Provider, Scope, alias, make_container, provide
from dishka.exceptions import InvalidGraphError


class AliasProvider(Provider):
    @provide(scope=Scope.APP)
    def provide_int(self) -> int:
        return 42

    aliased_complex = alias(source=float, provides=complex)
    aliased_float = alias(source=int, provides=float)


def test_alias():
    container = make_container(AliasProvider())
    assert container.get(float) == container.get(int)


def test_alias_to_alias():
    container = make_container(AliasProvider())
    assert container.get(complex) == container.get(int)


class CycleProvider(Provider):
    a = alias(source=int, provides=bool)
    b = alias(source=bool, provides=float)
    c = alias(source=float, provides=int)


def test_cycle():
    with pytest.raises(InvalidGraphError):
        make_container(CycleProvider())
