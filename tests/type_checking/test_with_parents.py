from dishka import (
    Provider,
    Scope,
    WithParents,
)


class Service:
    pass


class ServiceImpl(Service):
    pass


def get_service() -> WithParents[ServiceImpl]:
    return ServiceImpl()


service: ServiceImpl = get_service()

provider = Provider(scope=Scope.APP)
provider.provide(get_service, provides=WithParents[ServiceImpl])
