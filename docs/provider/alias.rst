.. _alias:

alias
****************

``alias`` is used to allow retrieving of the same object by different type hints. E.g. you have configured how to provide ``A`` object and want to use it as AProtocol: ``container.get(A)==container.get(AProtocol)``.

Provider object has also a ``.alias`` method with the same logic.

.. code-block:: python

    from dishka import alias, provide, Provider, Scope

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...

    class MyProvider(Provider):
        user_dao = provide(UserDAOImpl, scope=Scope.REQUEST)
        user_dao_proto = alias(source=UserDAOImpl, provides=UserDAO)

Additionally, alias has own setting for caching: it caches by default regardless if source is cached. You can disable it providing ``cache=False`` argument.

Do you want to override the alias? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container.

.. code-block:: python

    from dishka import provide, Provider, Scope, alias, make_container

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...
    class UserDAOMock(UserDAO): ...

    class MyProvider(Provider):
        scope = Scope.APP  # should be REQUEST, but set to APP for the sake of simplicity

        user_dao = provide(UserDAOImpl)
        user_dao_mock = provide(UserDAOMock)

        user_dao_proto = alias(UserDAOImpl, provides=UserDAO)
        user_dao_override = alias(
            UserDAOMock, provides=UserDAO, override=True
        )

    container = make_container(MyProvider())
    dao = container.get(UserDAO)  # UserDAOMock
