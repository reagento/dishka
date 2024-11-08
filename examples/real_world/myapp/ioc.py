from typing import Iterable

from dishka import (
    Provider,
    Scope,
    alias,
    provide,
)
from .api_client import FakeWarehouseClient
from .db import FakeCommiter, FakeProductGateway, FakeUserGateway
from .use_cases import (
    AddProductsInteractor,
    ProductGateway,
    Commiter,
    UserGateway,
    WarehouseClient,
)


# app dependency logic
class AdaptersProvider(Provider):
    scope = Scope.REQUEST

    users = provide(FakeUserGateway, provides=UserGateway)
    products = provide(FakeProductGateway, provides=ProductGateway)

    @provide
    def connection(self) -> Iterable[FakeCommiter]:
        commiter = FakeCommiter()
        yield commiter
        commiter.close()

    commiter = alias(source=FakeCommiter, provides=Commiter)

    @provide(scope=Scope.APP)
    def warehouse(self) -> WarehouseClient:
        return FakeWarehouseClient()


class InteractorProvider(Provider):
    scope = Scope.REQUEST

    product = provide(AddProductsInteractor)
