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
    users = provide(
        FakeUserGateway, scope=Scope.REQUEST, provides=UserGateway,
    )
    products = provide(
        FakeProductGateway, scope=Scope.REQUEST, provides=ProductGateway,
    )

    @provide(scope=Scope.REQUEST)
    def connection(self) -> Iterable[FakeDbConnection]:
        uow = FakeDbConnection()
        yield uow
        uow.close()

    uow = alias(source=FakeDbConnection, provides=UnitOfWork)

    @provide(scope=Scope.APP)
    def warehouse(self) -> WarehouseClient:
        return FakeWarehouseClient()


class InteractorProvider(Provider):
    product = provide(AddProductsInteractor, scope=Scope.REQUEST)
