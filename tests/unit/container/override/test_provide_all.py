import pytest

from dishka import Provider, Scope, make_container, provide_all
from dishka.entities.validation_settigs import STRICT_VALIDATION
from dishka.exceptions import ImplicitOverrideDetectedError


def test_not_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str)
        )

    with pytest.raises(ImplicitOverrideDetectedError):
        make_container(
            TestProvider(),
            validation_settings=STRICT_VALIDATION,
        )


def test_override() -> None:
    class TestProvider(Provider):
        scope = Scope.APP
        provides = (
            provide_all(int, str)
            + provide_all(int, str, override=True)
        )

    make_container(
        TestProvider(),
        validation_settings=STRICT_VALIDATION,
    )
