from dishka import Provider, Scope

from grpcio.services.uuid_service import UUIDService, UUIDServiceImpl


def service_provider() -> Provider:
    provider = Provider()

    provider.provide(
        UUIDServiceImpl,
        scope=Scope.REQUEST,
        provides=UUIDService,
    )

    return provider
