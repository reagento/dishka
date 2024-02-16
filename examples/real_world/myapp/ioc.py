from typing import Iterable

from dishka import (
    Provider,
    Scope,
    provide, alias,
)
from .api_client import FakeWarehouseClient
from .db import FakeProductGateway, FakeDbConnection, FakeUserGateway
from .use_cases import (
    AddProductsInteractor,
    ProductGateway,
    UnitOfWork,
    UserGateway,
    WarehouseClient,
)


# app dependency logic
class AdaptersProvider(Provider):
    scope = Scope.REQUEST

    users = provide(FakeUserGateway, provides=UserGateway)
    products = provide(FakeProductGateway, provides=ProductGateway)

    @provide
    def connection(self) -> Iterable[FakeDbConnection]:
        uow = FakeDbConnection()
        yield uow
        uow.close()

    uow = alias(source=FakeDbConnection, provides=UnitOfWork)

    @provide(scope=Scope.APP)
    def warehouse(self) -> WarehouseClient:
        return FakeWarehouseClient()


class InteractorProvider(Provider):
    scope = Scope.REQUEST

    product = provide(AddProductsInteractor)
