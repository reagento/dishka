import pytest

from dishka import ActivationContext, Has, Provider, Scope, make_container
from dishka.exceptions import NoFactoryError


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
    p = Provider()
    p.provide(lambda: 42, provides=provides, scope=Scope.APP)
    p.provide(lambda: "default", provides=str, scope=Scope.APP)
    p.provide(lambda: "int", provides=str, scope=Scope.APP, when=Has(int))
    p.provide(lambda: "float", provides=str, scope=Scope.APP, when=Has(float))
    c = make_container(p)

    assert c.get(str) == value


def test_has_cycle():
    p = Provider()
    p.provide(lambda: 42, provides=int, scope=Scope.APP, when=Has(str))
    p.provide(lambda: "s", provides=str, scope=Scope.APP, when=Has(int))
    c = make_container(p)
    assert c.get(str) == "s"
    assert c.get(int) == 42

def test_chain():
    p = Provider()
    p.provide(lambda: 42, provides=int, scope=Scope.APP, when=never)
    p.provide(lambda: "s", provides=str, scope=Scope.APP, when=Has(int))
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)
    with pytest.raises(NoFactoryError):
        c.get(str)


def test_custom_predicate_on():
    p = Provider()
    p.provide(lambda: 42, provides=int, scope=Scope.APP, when=always)
    p.from_context(provides=str, scope=Scope.APP, when=always)
    p.alias(int, provides=float, when=always)

    c = make_container(p, context={str: "x"})
    assert c.get(int) == 42
    assert c.get(str) == "x"
    assert c.get(float) == 42


def test_custom_predicate_off():
    p = Provider()
    p.provide(lambda: 42, provides=int, scope=Scope.APP, when=never)
    p.from_context(provides=str, scope=Scope.APP, when=never)
    p.alias(int, provides=float, when=never)
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)
    with pytest.raises(NoFactoryError):
        c.get(str)
    with pytest.raises(NoFactoryError):
        c.get(float)


def test_provider():
    p1 = Provider()
    p1.provide(lambda: 1, provides=int, scope=Scope.APP)
    p2 = Provider(when=always)
    p2.provide(lambda: 2, provides=int, scope=Scope.APP, when=never)
    p3 = Provider(when=never)
    p3.provide(lambda: 3, provides=int, scope=Scope.APP, when=always)
    c = make_container(p1, p2, p3)
    assert c.get(int) == 1


def test_provider_class_when():
    class MyProvide(Provider):
        def when(self, x: ActivationContext) -> bool:
            return False

    p = MyProvide()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    c = make_container(p)
    with pytest.raises(NoFactoryError):
        c.get(int)


def add(x: int) -> int:
    return x + 1


def neg(x: int) -> int:
    return -x


def test_decorator():
    p = Provider()
    p.provide(lambda: 1, provides=int, scope=Scope.APP)
    p.decorate(add, when=always)
    p.decorate(neg, when=never)

    c = make_container(p)
    assert c.get(int) == 2
