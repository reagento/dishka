"""
In this test file we use DIshka to provide mocked adapters
though it is not necessary as our interactor is not bound to library
"""

from unittest.mock import Mock

import pytest

from dishka import (
    Provider,
    Scope,
    make_container,
    provide,
)

from myapp.ioc import InteractorProvider
from myapp.use_cases import (
    AddProductsInteractor,
    ProductGateway,
    UnitOfWork,
    User,
    UserGateway,
    WarehouseClient,
)


# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.APP)
    def users(self) -> UserGateway:
        gateway = Mock()
        gateway.get_user = Mock(return_value=User())
        return gateway

    @provide(scope=Scope.APP)
    def products(self) -> ProductGateway:
        gateway = Mock()
        gateway.add_product = Mock()
        return gateway

    @provide(scope=Scope.APP)
    def uow(self) -> UnitOfWork:
        uow = Mock()
        uow.commit = Mock()
        return uow

    @provide(scope=Scope.APP)
    def warehouse(self) -> WarehouseClient:
        warehouse = Mock()
        warehouse.next_product = Mock(return_value=["a", "b"])
        return warehouse


@pytest.fixture
def container():
    with make_container(AdaptersProvider(), InteractorProvider()) as c:
        with c() as request_c:
            yield request_c


def test_interactor(container):
    interactor = container.get(AddProductsInteractor)
    interactor(1)
    container.get(UnitOfWork).commit.assert_called_once_with()
