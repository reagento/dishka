from grpcio.services.uuid_service import UUIDService, UUIDServiceImpl

from dishka import Provider, Scope, provide


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    @provide(provides=UUIDService)
    def service_factory(self) -> UUIDServiceImpl:
        return UUIDServiceImpl()
