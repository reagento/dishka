import pytest

from dishka import Provider, Scope, make_container, provide, provide_all
from dishka.exceptions import FactoryIsNotOverriddenError


def test_not_override_provide() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide(source=int, provides=int)
            + provide(source=int, provides=int)
            + provide(source=str, provides=str)
            + provide(source=str, provides=str)
        )

    with pytest.raises(FactoryIsNotOverriddenError):
        make_container(TestProvider())
