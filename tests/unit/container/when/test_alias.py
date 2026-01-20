from dataclasses import dataclass

from dishka import Marker, Provider, Scope, make_container


def test_marker_alias():
    provider = Provider(scope=Scope.APP)
    provider.activator(lambda: True, Marker("A"))
    provider.alias(source=Marker("A"), provides=Marker("B"))
    provider.provide(lambda: 1, provides=int)
    provider.provide(lambda: 2, provides=int, when=Marker("B"))

    c = make_container(provider)
    assert c.get(int) == 2


def activator_x(activator_dep: int, marker: Marker) -> bool:
    return activator_dep == 42 and marker == Marker("A")


def test_marker_alias_component():
    provider_x = Provider(scope=Scope.APP, component="X")
    provider_x.provide(lambda: 42, provides=int)
    provider_x.activator(activator_x, Marker("A"))

    provider = Provider(scope=Scope.APP)
    provider.alias(source=Marker("A"), provides=Marker("B"), component="X")
    provider.provide(lambda: 1, provides=int)
    provider.provide(lambda: 2, provides=int, when=Marker("B"))

    c = make_container(provider_x, provider)
    assert c.get(int) == 2


@dataclass(frozen=True, slots=True)
class MyMarker(Marker):
    pass


def myactivator_x(activator_dep: int, marker: MyMarker) -> bool:
    return activator_dep == 42 and marker == MyMarker("B")


def test_marker_type_alias_component():
    provider_x = Provider(scope=Scope.APP, component="X")
    provider_x.provide(lambda: 42, provides=int)
    provider_x.activator(myactivator_x, MyMarker)

    provider = Provider(scope=Scope.APP)
    provider.alias(source=MyMarker, component="X")
    provider.provide(lambda: 1, provides=int)
    provider.provide(lambda: 2, provides=int, when=MyMarker("B"))

    c = make_container(provider_x, provider)
    assert c.get(int) == 2
