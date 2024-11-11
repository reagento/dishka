"""
In this test file we use DIshka to provide mocked adapters
though it is not necessary as our interactor is not bound to library
"""

from unittest.mock import Mock

import pytest
from myapp.ioc import InteractorProvider
from myapp.use_cases import (
    AddProductsInteractor,
    Committer,
    ProductGateway,
    User,
    UserGateway,
    WarehouseClient,
)

from dishka import (
    Provider,
    Scope,
    make_container,
    provide,
)


# app dependency logic
class AdaptersProvider(Provider):
    scope = Scope.APP

    @provide
    def users(self) -> UserGateway:
        gateway = Mock()
        gateway.get_user = Mock(return_value=User())
        return gateway

    @provide
    def products(self) -> ProductGateway:
        gateway = Mock()
        gateway.add_product = Mock()
        return gateway

    @provide
    def committer(self) -> Committer:
        committer = Mock()
        committer.commit = Mock()
        return committer

    @provide
    def warehouse(self) -> WarehouseClient:
        warehouse = Mock()
        warehouse.next_product = Mock(return_value=["a", "b"])
        return warehouse


@pytest.fixture
def container():
    c = make_container(AdaptersProvider(), InteractorProvider())
    with c() as request_c:
        yield request_c


def test_interactor(container):
    interactor = container.get(AddProductsInteractor)
    interactor(1)
    container.get(Committer).commit.assert_called_once_with()
