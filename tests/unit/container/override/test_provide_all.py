import pytest

from dishka import (
    STRICT_VALIDATION,
    Provider,
    Scope,
    make_container,
    provide_all,
)
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
