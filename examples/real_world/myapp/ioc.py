from collections.abc import Iterable

from dishka import (
    Provider,
    Scope,
    alias,
    provide,
)

from .api_client import FakeWarehouseClient
from .db import FakeCommitter, FakeProductGateway, FakeUserGateway
from .use_cases import (
    AddProductsInteractor,
    Committer,
    ProductGateway,
    UserGateway,
    WarehouseClient,
)


# app dependency logic
class AdaptersProvider(Provider):
    scope = Scope.REQUEST

    users = provide(FakeUserGateway, provides=UserGateway)
    products = provide(FakeProductGateway, provides=ProductGateway)

    @provide
    def connection(self) -> Iterable[FakeCommitter]:
        committer = FakeCommitter()
        yield committer
        committer.close()

    committer = alias(source=FakeCommitter, provides=Committer)

    @provide(scope=Scope.APP)
    def warehouse(self) -> WarehouseClient:
        return FakeWarehouseClient()


class InteractorProvider(Provider):
    scope = Scope.REQUEST

    product = provide(AddProductsInteractor)
