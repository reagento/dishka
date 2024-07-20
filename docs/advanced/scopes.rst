.. include:: <isonum.txt>
.. _scopes:

Scope management
*************************

In dishka scope determines a lifespan of dependency. Firstly, when creating provider, your attach dependency to its scope. Then, when you use container you enter scope and dependency is retained once it is requested until you exist that scope.

The set of scopes is defined once per container and providers should use the same scopes. You are not limited to standard scopes and can create custom ones, but it is hardly ever needed.

In most cases you need only 2 scopes. ``APP``-scope is usually entered on container creation and ``REQUEST``-scope is the one you go into during some event processing:

    ``APP`` |rarr| ``REQUEST``

But standard set is much wider. Dishka supported *skipped* scopes and has just 2 additional just in case:

    ``[RUNTIME]`` |rarr| ``APP`` |rarr| ``[SESSION]`` |rarr| ``REQUEST`` |rarr| ``ACTION`` |rarr| ``STEP``

Entering container context will bring you to the next non-skipped scope. Or to the target scope if you provided one.

Skipped scopes
======================

Skipped scope in the scope which is implicitly passed through when you are going deeper from parent container.


For example, standard scopes ``RUNTIME`` and ``SESSION`` are marked as ``skip=True``:

When you create a container, you implicitly enter ``APP``-scope. ``RUNTIME`` scope is still used, you can have dependencies attached to it, but it is entered automatically and also closed once you close ``APP``-scoped container.

.. code-block:: python

    container = make_container(provider)  # APP

In other case you can enter ``RUNTIME`` scope passing ``start_scope=Scope.RUNTIME`` when entering container and you will get that scope. When you go deeper you will enter ``APP`` scope as it is the next appropriate one. In that case, closing ``APP`` scope won't close ``RUNTIME`` as it was entered explicitly.

.. code-block:: python

    container = make_container(provider, start_scope=Scope.RUNTIME)
    with container() as app_container:
        # RUNTIME -> APP

The same thing is about going into when you are in ``APP`` scope. If you just call ``with container()`` you will skip ``SESSION`` scope and go into ``REQUEST`` one. Both will be closed simultaneously. Calling ``with container(scope=Scope.SESSION)`` will bring you to that scope and you can go into ``REQUEST`` with the next call.


.. code-block:: python

    container = make_container(provider)
    with container() as request_container:
        # APP -> Session -> REQUEST
        pass

    with container(scope=Scope.SESSION) as session_container:
        # APP -> Session
        with session_container() as request_container:
            # Session -> REQUEST
            pass

.. note::

    * ``RUNTIME`` scope can be useful for adding dependencies which are kept between tests recreating apps.
    * ``SESSION`` scope can be useful for connection related objects in websockets, while HTTP-request handler goes straight into ``REQUEST`` scope.

Custom scopes
======================

To create a custom scopes set you need

* inherit from ``BaseScope``
* set scopes using ``new_scope()``
* provide that scope class to ``make_container`` call as a ``scopes=`` argument

.. code-block:: python

    from dishka import BaseScope, Provider, make_container, new_scope

    class MyScope(BaseScope):
        APPLICATION = new_scope("APPLICATION")
        SESSION = new_scope("SESSION", skip=True)
        EVENT = new_scope("EVENT")

    provider = Provider(scope=MyScope.EVENT)
    make_container(provider, scopes=MyScope)