import pytest

from dishka import (
    Marker,
    Provider,
    Scope,
    activate,
    alias,
    decorate,
    make_container,
    provide,
)


@pytest.mark.parametrize(
    ("provider_active", "expected"),
    [(True, "conditional"), (False, "default")],
)
def test_factory_inherits_provider_when(provider_active, expected):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "default"

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @provide
        def get_value(self) -> str:
            return "conditional"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("provider_active", "factory_active", "expected"),
    [
        (True, True, "both_active"),
        (True, False, "default"),
        (False, True, "default"),
        (False, False, "default"),
    ],
)
def test_factory_combines_when_with_provider(
    provider_active, factory_active, expected,
):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "default"

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @provide(when=Marker("factory"))
        def get_value(self) -> str:
            return "both_active"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))
    activator.activate(lambda: factory_active, Marker("factory"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("factory_active", "expected"),
    [(True, "factory_when"), (False, "default")],
)
def test_factory_when_without_provider_when(factory_active, expected):
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_default(self) -> str:
            return "default"

        @provide(when=Marker("factory"))
        def get_conditional(self) -> str:
            return "factory_when"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: factory_active, Marker("factory"))

    container = make_container(MyProvider(), activator)
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("provider_active", "expected"),
    [(True, "decorated:base"), (False, "base")],
)
def test_decorator_inherits_provider_when(provider_active, expected):
    class BaseProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "base"

    class DecoratorProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @decorate
        def wrap(self, value: str) -> str:
            return f"decorated:{value}"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))

    container = make_container(
        BaseProvider(), DecoratorProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("provider_active", "decorator_active", "expected"),
    [
        (True, True, "decorated:base"),
        (True, False, "base"),
        (False, True, "base"),
        (False, False, "base"),
    ],
)
def test_decorator_combines_when_with_provider(
    provider_active, decorator_active, expected,
):
    class BaseProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "base"

    class DecoratorProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @decorate(when=Marker("decorator"))
        def wrap(self, value: str) -> str:
            return f"decorated:{value}"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))
    activator.activate(lambda: decorator_active, Marker("decorator"))

    container = make_container(
        BaseProvider(), DecoratorProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("decorator_active", "expected"),
    [(True, "decorated:base"), (False, "base")],
)
def test_decorator_when_without_provider_when(decorator_active, expected):
    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "base"

        @decorate(when=Marker("decorator"))
        def wrap(self, value: str) -> str:
            return f"decorated:{value}"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: decorator_active, Marker("decorator"))

    container = make_container(MyProvider(), activator)
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("marker_a_active", "marker_b_active", "expected"),
    [
        (True, True, "conditional"),
        (True, False, "conditional"),
        (False, True, "conditional"),
        (False, False, "default"),
    ],
)
def test_provider_when_or_expression(
    marker_a_active, marker_b_active, expected,
):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "default"

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("a") | Marker("b")

        @provide
        def get_value(self) -> str:
            return "conditional"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: marker_a_active, Marker("a"))
    activator.activate(lambda: marker_b_active, Marker("b"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("marker_a_active", "marker_b_active", "expected"),
    [
        (True, True, "conditional"),
        (True, False, "default"),
        (False, True, "default"),
        (False, False, "default"),
    ],
)
def test_provider_when_and_expression(
    marker_a_active, marker_b_active, expected,
):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_value(self) -> str:
            return "default"

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("a") & Marker("b")

        @provide
        def get_value(self) -> str:
            return "conditional"

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: marker_a_active, Marker("a"))
    activator.activate(lambda: marker_b_active, Marker("b"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(str) == expected


@pytest.mark.parametrize(
    ("provider_active", "expected"),
    [(True, 1.0), (False, 0.0)],
)
def test_alias_inherits_provider_when(provider_active, expected):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 0

        @provide
        def get_float(self) -> float:
            return 0.0

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @provide
        def get_int(self) -> int:
            return 1

        float_alias = alias(source=int, provides=float)

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(float) == expected


@pytest.mark.parametrize(
    ("provider_active", "alias_active", "expected"),
    [
        (True, True, 1.0),
        (True, False, 0.0),
        (False, True, 0.0),
        (False, False, 0.0),
    ],
)
def test_alias_combines_when_with_provider(
    provider_active, alias_active, expected,
):
    class DefaultProvider(Provider):
        scope = Scope.APP

        @provide
        def get_int(self) -> int:
            return 0

        @provide
        def get_float(self) -> float:
            return 0.0

    class ConditionalProvider(Provider):
        scope = Scope.APP
        when = Marker("provider")

        @provide
        def get_int(self) -> int:
            return 1

        float_alias = alias(
            source=int, provides=float, when=Marker("alias"),
        )

    activator = Provider(scope=Scope.APP)
    activator.activate(lambda: provider_active, Marker("provider"))
    activator.activate(lambda: alias_active, Marker("alias"))

    container = make_container(
        DefaultProvider(), ConditionalProvider(), activator,
    )
    assert container.get(float) == expected


def test_activate_in_provider_with_when_no_recursion():
    class TestProvider(Provider):
        when = Marker("debug")
        scope = Scope.APP

        @activate(Marker("debug"))
        def is_debug(self) -> bool:
            return True

        @provide()
        def provide_int(self) -> int:
            return 1

    container = make_container(TestProvider())
    assert container.get(int) == 1
