Container
*******************

**Container** is an object you use to get your dependency.

Basic usage
======================


Container can be synchronous or asynchronous.

* *Async* container can use any type of dependency sources: both sync and async are supported. Sync methods are called directly and no executors are used, so avoid network I/O in synchronous functions
* *Sync* container can use only synchronous dependency sources.

To create a top level container you should call ``make_container`` (or ``make_async_container``). Pass there one or more providers.

.. code-block:: python

    from dishka import make_container
    container = make_container(provider)

And async version correspondingly:

.. code-block:: python

    from dishka import make_container

    container = await make_async_container(provider)

If you have not provided your own *scopes* enum, then default one will be used. Root container is attached to the first scope: Scope.APP by default.

To enter the next scope you should call container as a function and enter context manager:

.. code-block:: python

    with container() as nested_container:
        pass

or if you created *async* container:

.. code-block:: python

    async with container() as nested_container:
        pass

Container is needed for retrieving objects. To do it you need to call ``get(DependencyType)`` (and ``await`` it for async container).
All retrieved dependencies are stored inside container of corresponding scope until you exit that scope. So, you if you call ``get`` multiple times you will receive the same instance. The rule is followed for indirect dependencies as well. Multiple dependencies of the same scope have their own cache.

.. code-block:: python

    container = make_container(provider)
    a = container.get(A)
    a = container.get(A)  # same instance

And async:

.. code-block:: python

    container = make_async_container(provider)
    a = await container.get(A)
    a = await container.get(A)  # same instance

When you exit the scope, dependency cache is cleared. Finalization of dependencies is done if you used generator factories.

APP-level container is not a context manager, so call ``.close()`` on your app termination

.. code-block:: python

    container.close()

And async:

.. code-block:: python

    await container.close()


Thread/task safety
==========================

You can have multiple containers of the same scope simultaneously (except the top level one) - it is safe while you do not have dependencies of previous scope.

For example, if you have declared ``SessionPool`` as an APP-scoped dependency and then you concurrently enter REQUEST scope. Once you request ``SessionPool`` for the first time (directly or for another dependency) you cannot guarantee that only one instance of that object is created.

To prevent such a condition you need to protect any session whose children can be used concurrently: to pass ``lock_factory`` when creating a container. Do not mix up threading and asyncio locks: they are not interchangeable, use the proper one.

.. code-block:: python

    import threading

    container = make_container(provider, lock_factory=threading.Lock):
    with container(lock_factory=threading.Lock) as nested_container:
        ...

.. code-block:: python

    import asyncio

    container = await make_async_container(provider, lock_factory=asyncio.Lock)
    async with container(lock_factory=asyncio.Lock) as nested_container:
        ...


.. note::
    Do not worry, lock is set by default for top level (``Scope.APP``) container. So, if you are not using other scopes concurrently you do not need any changes. (E.g. if you are not using multiple ``Scope.ACTION`` containers at a same time within one ``Scope.REQUEST`` container)

Context data
====================

Often, your scopes are assigned with some external events: HTTP-requests, message from queue, callbacks from framework. You can use those objects when creating dependencies. The difference from normal factories is that they are not created inside some ``Provider``, but passed to the scope:

.. code-block:: python

    from framework import Request

    class MyProvider:
        @provide(scope=Scope.REQUEST)
        def a(self, request: Request) -> A:
            return A(data=request.contents)

    container = make_container(MyProvider())

    while True:
        request = connection.recv()
        with container(context={Request:request}) as request_container:
             a = request_container.get(A)
