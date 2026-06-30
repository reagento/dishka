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

.. note::

   More patterns (configuration, resources/finalization, wiring, and test
   overrides) will be added to this guide as they are written. See
   `issue #402 <https://github.com/reagento/dishka/issues/402>`_ for the
   full list of planned sections.
```