from typing import Protocol

import pytest

from dishka import make_container, Provider, Scope, WithProtocols
from dishka.exceptions import NoFactoryError


class AProtocol(Protocol):
    pass


class BProtocol(Protocol):
    pass


class C(AProtocol, BProtocol):
    pass


def test_get_parents_protocols() -> None:
    provider = Provider(scope=Scope.APP)
    provider.provide(C, provides=WithProtocols[C])
    container = make_container(provider)
    
    assert (
        container.get(BProtocol)
        is container.get(AProtocol)
    )


def test_get_by_not_protocol() -> None:
    provider = Provider(scope=Scope.APP)
    provider.provide(C, provides=WithProtocols[C])
    container = make_container(provider)
    
    with pytest.raises(NoFactoryError):
        container.get(C)