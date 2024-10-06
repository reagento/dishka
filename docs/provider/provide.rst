.. _provide:

provide
******************

``provide`` function is used to declare a factory providing a dependency. It can be used with some class or as a method decorator (either sync or async). It supports finalization of dependency if you make it a generator.

Provider object has also a ``.provide`` method with the same logic.

If it is used with class, it analyzes its ``__init__`` typehints to detect its dependencies. If it is used with method, it checks its parameters typehints and a result type. Last one describes what this method is used to create.

``scope`` argument is required to define the lifetime of the created object.
By default the result is cached within scope. You can disable it providing ``cache=False`` argument.

* For simple case add method and mark it with ``@provide`` decorator.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

* Want some finalization when exiting the scope? Make that method generator:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            yield a
            a.close()

Also, if an error occurs during process handling (inside the ``with`` block), it will be sent to the generator:

.. code-block:: python

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            exc = yield a
            # exc will be None if an exception has not occurred
            if exc:
                print("Some exception while process handling: ", exc)
            a.close()

* Do not have any specific logic and just want to create class using its ``__init__``? Then add a provider attribute using ``provide`` as function passing that class.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        a = provide(A, scope=Scope.REQUEST)

* Want to create a child class instance when parent is requested? Add a ``source`` attribute to ``provide`` function with a parent class while passing child as a first parameter

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        a = provide(source=AChild, scope=Scope.REQUEST, provides=A)


* Want to go ``async``? Make provide methods asynchronous. Create async container. Use ``async with`` and await ``get`` calls:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       @provide(scope=Scope.APP)
       async def get_a(self) -> A:
          return A()

    container = make_async_container(MyProvider())
    a = await container.get(A)

* Tired of providing ``scope=`` for each dependency? Set it inside your ``Provider`` class and all factories with no scope will use it.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       scope=Scope.APP

       @provide  # uses provider scope
       async def get_a(self) -> A:
          return A()

       @provide(scope=Scope.REQUEST)  # has own scope
       async def get_b(self) -> B:
          return B()

* Having multiple interfaces which can be created as a same class? Use ``AnyOf`` as a result hint:

.. code-block:: python

    from dishka import AnyOf, provide, Provider, Scope

    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def p(self) -> AnyOf[A, AProtocol]:
            return A()

It works similar to :ref:`alias`.

* Do you want to get dependencies by parents? Use ``WithParents`` as a result hint:

.. code-block:: python

    from dishka import WithParents, provide, Provider, Scope

    class A(Protocol): ...
    class AImpl(A): ...

    class MyProvider(Provider):
        scope=Scope.APP

        @provide
        def a(self) -> WithParents[AImpl]:
            return A()

    container = make_async_container(MyProvider())
    a = await container.get(A)
    a = await container.get(AImpl)
    a is a # True


WithParents generates only one factory and many aliases and is equivalent to ``AnyOf[AImpl, A]``. The following parents are ignored: ``type``, ``object``, ``Enum``, ``ABC``, ``ABCMeta``, ``Generic``, ``Protocol``, ``Exception``, ``BaseException``

* You object's dependencies (and their dependencies) can be simply created by calling their constructors. You do not need to register them manually. Use ``recursive=True`` to register them automatically

.. code-block:: python

    class A: ...

    class B:
        def __init__(self, a: A): ...

    class C:
        def __init__(self, b: B): ...

    class MyProvider(Provider):
        c = provide(C, scope=Scope.APP, recursive=True)


* Do you want to override the factory? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container.

.. code-block:: python

    from dishka import WithParents, provide, Provider, Scope
    class MyProvider(Provider):
        scope=Scope.APP
        a = provide(lambda: 1, provides=int)
        a_override = provide(lambda: 2, provides=int, override=True)
    container = make_async_container(MyProvider())
    a = await container.get(int)
    # 2


* You can use factory with Generic classes

.. code-block:: python

    class MyProvider(Provider):
        @provide
        def make_a(self, type_: type[T]) -> A[T]:
            ...

