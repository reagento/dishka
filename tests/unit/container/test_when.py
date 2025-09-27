import pytest

from dishka import (
    ActivationContext,
    Has,
    Provider,
    Scope,
    alias,
    decorate,
    from_context,
    make_container,
    provide,
    provide_all,
)
from dishka.exceptions import NoFactoryError


class A:
    pass

class B:
    pass

def always(x: ActivationContext) -> bool:
    return True


def never(x: ActivationContext) -> bool:
    return False


@pytest.mark.parametrize(
    ("provides", "value"), [
        (int, "int"),
        (float, "float"),
        (complex, "default"),
    ],
)
def test_has_cls(provides, value):
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 42, provides=provides)
    p.provide(lambda: "default", provides=str)
    p.provide(lambda: "int", provides=str, when=Has(int))
    p.provide(lambda: "float", provides=str, when=Has(float))
    c = make_container(p)

    assert c.get(str) == value


def test_has_cycle():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 42, provides=int, when=Has(str))
    p.provide(lambda: "s", provides=str, when=Has(int))
    c = make_container(p)
    assert c.get(str) == "s"
    assert c.get(int) == 42


def test_chain():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 42, provides=int, when=never)
    p.provide(lambda: "s", provides=str, when=Has(int))
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)
    with pytest.raises(NoFactoryError):
        c.get(str)


def test_custom_predicate_on():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 42, provides=int, when=always)
    p.from_context(provides=str, when=always)
    p.alias(int, provides=float, when=always)
    p.provide_all(A, B, when=always)

    c = make_container(p, context={str: "x"})
    assert c.get(int) == 42
    assert c.get(str) == "x"
    assert c.get(float) == 42
    assert isinstance(c.get(A), A)
    assert isinstance(c.get(B), B)


def test_custom_predicate_off():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 42, provides=int, when=never)
    p.from_context(provides=str, when=never)
    p.alias(int, provides=float, when=never)
    p.provide_all(A, B, when=never)
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)
    with pytest.raises(NoFactoryError):
        c.get(str)
    with pytest.raises(NoFactoryError):
        c.get(float)
    with pytest.raises(NoFactoryError):
        c.get(A)
    with pytest.raises(NoFactoryError):
        c.get(B)


def test_provider():
    p1 = Provider(scope=Scope.APP)
    p1.provide(lambda: 1, provides=int)
    p2 = Provider(scope=Scope.APP, when=always)
    p2.provide(lambda: 2, provides=int, when=never)
    p3 = Provider(scope=Scope.APP, when=never)
    p3.provide(lambda: 3, provides=int, when=always)
    c = make_container(p1, p2, p3)
    assert c.get(int) == 1


def test_provider_class_when():
    class MyProvide(Provider):
        def when(self, x: ActivationContext) -> bool:
            return False

    p = MyProvide(scope=Scope.APP)
    p.provide(lambda: 1, provides=int)
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)


def add(x: int) -> int:
    return x + 1


def neg(x: int) -> int:
    return -x


def test_decorator():
    p = Provider(scope=Scope.APP)
    p.provide(lambda: 1, provides=int)
    p.decorate(add, when=always)
    p.decorate(neg, when=never)

    c = make_container(p)
    assert c.get(int) == 2


def test_class_based():
    class MyProvide(Provider):
        scope = Scope.APP

        @provide
        def b(self) -> complex:
            return 42

        @provide(when=never)
        def i(self) -> int:
            return 1

        a = alias(complex, provides=float, when=never)
        s  = from_context(str, when=never)

        @decorate(when=never)
        def d(self, value: complex) -> complex:
            return value * 100

        x = provide_all(A, B, when=never)

    p = MyProvide()
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)
    with pytest.raises(NoFactoryError):
        c.get(float)
    with pytest.raises(NoFactoryError):
        c.get(str)
    with pytest.raises(NoFactoryError):
        c.get(A)
    with pytest.raises(NoFactoryError):
        c.get(B)
    assert c.get(complex) == 42
