from dishka import Provider, Scope


service_provider = Provider(scope=Scope.REQUEST)
service_provider.provide(Service)
service_provider.provide(DBGateway)
service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope
