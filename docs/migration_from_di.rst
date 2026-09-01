```restructuredtext
Migration from dependency-injector
===================================

This guide helps you translate common ``dependency-injector`` patterns into
their Dishka equivalents. It assumes you are already familiar with Dishka's
basic concepts (Container and Provider).

Containers and factories
-------------------------

With ``dependency-injector``, you typically declare a container with
``providers.Factory`` for objects that should be created fresh on every
request:

.. code-block:: python

    # dependency-injector
    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        api_client = providers.Factory(APIClient)
        user_dao = providers.Factory(SQLiteUserDAO, connection=...)
        service = providers.Factory(Service, client=api_client, user_dao=user_dao)

With Dishka, you register the same classes on a ``Provider``, and dependencies
are resolved automatically from type hints rather than being wired by hand:

.. code-block:: python

    # dishka
    from dishka import Provider, Scope

    service_provider = Provider(scope=Scope.REQUEST)
    service_provider.provide(Service)
    service_provider.provide(SQLiteUserDAO, provides=UserDAO)
    service_provider.provide(APIClient)

Notice there's no need to manually pass ``client=api_client`` — Dishka
inspects ``Service.__init__`` and resolves ``APIClient`` and ``UserDAO``
on its own.

Singletons
----------

``dependency-injector`` uses ``providers.Singleton`` for objects that should
be created once and reused for the application's lifetime:

.. code-block:: python

    # dependency-injector
    api_client = providers.Singleton(APIClient)

In Dishka, this is expressed with ``Scope.APP`` instead of a distinct
provider type:

.. code-block:: python

    # dishka
    service_provider.provide(APIClient, scope=Scope.APP)

Any dependency scoped to ``Scope.APP`` is created once and reused across all
requests, just like a ``Singleton`` — but you set this per-dependency rather
than choosing a different provider class.


Configuration
--------------

``dependency-injector`` ships a dedicated ``providers.Configuration`` object
that can be populated from environment variables, YAML, or dictionaries, and
then injected into other providers:

.. code-block:: python

    # dependency-injector
    from dependency_injector import containers, providers

    class Container(containers.DeclarativeContainer):
        config = providers.Configuration()
        api_client = providers.Factory(
            APIClient,
            base_url=config.api.base_url,
        )

    container = Container()
    container.config.from_env("API_BASE_URL", as_=str)
    # or: container.config.from_yaml("config.yml")

Dishka has no dedicated configuration provider. Instead, you load your
configuration however you'd normally do it in plain Python (environment
variables, a settings library, a YAML loader, etc.), and provide the
resulting object like any other dependency:

.. code-block:: python

    # dishka
    from dataclasses import dataclass
    from dishka import Provider, Scope, provide

    @dataclass
    class ApiConfig:
        base_url: str

    class ConfigProvider(Provider):
        @provide(scope=Scope.APP)
        def get_config(self) -> ApiConfig:
            return ApiConfig(base_url=os.environ["API_BASE_URL"])

    service_provider.provide(APIClient)  # APIClient.__init__ takes ApiConfig

``APIClient`` simply declares ``ApiConfig`` as a constructor parameter, and
Dishka resolves it from ``ConfigProvider`` automatically — there's no
separate configuration "tree" to populate, since config is just another
typed dependency.

Resources and finalization
----------------------------

``dependency-injector`` has a ``providers.Resource`` type for dependencies
that need explicit setup and teardown — like a database connection that
must be closed when the app shuts down:

.. code-block:: python

    # dependency-injector
    from dependency_injector import containers, providers

    def init_connection():
        connection = sqlite3.connect(":memory:")
        yield connection
        connection.close()

    class Container(containers.DeclarativeContainer):
        connection = providers.Resource(init_connection)

In Dishka, there's no separate provider type for this — any ``@provide``
method can be written as a generator that ``yield``s the dependency, and
whatever code runs after the ``yield`` is treated as cleanup:

.. code-block:: python

    # dishka
    import sqlite3
    from collections.abc import Iterable
    from sqlite3 import Connection
    from dishka import Provider, Scope, provide

    class ConnectionProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def new_connection(self) -> Iterable[Connection]:
            connection = sqlite3.connect(":memory:")
            yield connection
            connection.close()

Dishka calls the cleanup code automatically when the relevant scope exits
(for example, when a ``with container() as request_container:`` block
ends) — you don't need to register finalizers separately, the same
function handles both creation and teardown.
Wiring (injecting dependencies into functions)
-------------------------------------------------

``dependency-injector`` uses the ``@inject`` decorator together with
``Provide[Container.x]`` markers to inject dependencies into function
parameters:

.. code-block:: python

    # dependency-injector
    from dependency_injector.wiring import inject, Provide

    @inject
    def process(service: Service = Provide[Container.service]) -> None:
        ...

    Container.wire(modules=[__name__])

Dishka also uses ``@inject``, but instead of a default-value marker tied to
a specific container, it uses a type annotation (``FromDishka[X]``) that
works independently of any one container instance:

.. code-block:: python

    # dishka
    from dishka import FromDishka
    from dishka.integrations.fastapi import inject

    @inject
    async def process(service: FromDishka[Service]) -> None:
        ...

For web frameworks, Dishka also provides a ``setup_dishka()`` call that
wires the container into the framework automatically (see the Quickstart
example with FastAPI) — there's no separate manual ``wire(modules=...)``
step.

Overriding dependencies for tests
------------------------------------

``dependency-injector`` lets you override a provider directly for testing:

.. code-block:: python

    # dependency-injector
    with Container.api_client.override(providers.Object(FakeAPIClient())):
        ...

In Dishka, you build a container with a test-specific provider in place of
the real one, since providers are just passed into ``make_container()``:

.. code-block:: python

    # dishka
    test_provider = Provider(scope=Scope.APP)
    test_provider.provide(FakeAPIClient, provides=APIClient)

    container = make_container(test_provider, ConnectionProvider())

This keeps the override explicit and scoped to the test container you
build, rather than mutating shared global container state.
