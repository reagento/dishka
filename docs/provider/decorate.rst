.. _decorate:

decorate
*********************

``decorate`` is used to modify or wrap an object which is already configured in another ``Provider``.

Provider object has also a ``.decorate`` method with the same logic.

If you want to apply decorator pattern and do not want to alter existing provide method, then it is a place for ``decorate``. It will construct object using earlier defined provider and then pass it to your decorator before returning from the container.


.. code-block:: python

    from dishka import decorate, Provider, provide, Scope

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...
    class UserDAOWithMetrics(UserDAO):
        def __init__(self, dao: UserDAO) -> None:
            self.dao = dao
            self.prometheus = Prometheus()
        def get_by_id(self, uid: UserID) -> User:
            self.prometheus.get_by_id_metric.inc()
            return self.dao.get_by_id(uid)

    class MyProvider(Provider):
        user_dao = provide(
            UserDAOImpl, scope=Scope.REQUEST, provides=UserDAO
        )
        @decorate
        def decorate_user_dao(self, dao: UserDAO) -> UserDAO:
            return UserDAOWithMetrics(dao)

Such decorator function can also have additional parameters.

.. code-block:: python

    from dishka import decorate, Provider, provide, Scope

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...
    class UserDAOWithMetrics(UserDAO):
        def __init__(self, dao: UserDAO, prom: Prometheus) -> None:
            self.dao = dao
            self.prometheus = prom
        def get_by_id(self, uid: UserID) -> User:
            self.prometheus.get_by_id_metric.inc()
            return self.dao.get_by_id(uid)

    class MyProvider(Provider):
        user_dao = provide(
            UserDAOImpl, scope=Scope.REQUEST, provides=UserDAO
        )
        prometheus = provide(Prometheus)

        @decorate
        def decorate_user_dao(
            self, dao: UserDAO, prom: Prometheus
        ) -> UserDAO:
            return UserDAOWithMetrics(dao, prom)

The limitation is that you cannot use ``decorate`` in the same provider as you declare factory or alias for dependency. But you won't need it because you can update the factory code.

The idea of ``decorate`` is to postprocess dependencies provided by some external source, when you combine multiple ``Provider`` objects into one container.