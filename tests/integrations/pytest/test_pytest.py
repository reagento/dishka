import pytest

from dishka import make_container, Provider, Scope, FromDishka


@pytest.fixture(scope="session")
def dishka_container():
    provider = Provider(scope=Scope.APP)
    provider.provide(source=lambda: 42, provides=int)
    return make_container(provider)


def test_xxx(value: FromDishka[int]) -> None:
    assert value == 42
