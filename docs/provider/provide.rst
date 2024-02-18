.. _provide:

@provide
******************

``provide`` function is used to declare a factory providing a dependency. It can be used with some class or as a method decorator. In second case it can be sync or async method. Also, it can support finalization of dependency if you make it a generator.

If it is used with class analyzes its ``__init__`` typehints to detect its dependencies. If it is used with method, it checks its parameters typehints and a result type. Last one describes what this method is used to create.

``scope`` argument is required to define the lifetime of the created object.
By default the result is cached within scope. You can disable it providing ``cache=False`` argument.

* For simple case add method and mark it with ``@provide`` decorator.

.. code-block:: python

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

* Want some finalization when exiting the scope? Make that method generator:

.. code-block:: python

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> Iterable[A]:
            a = A()
            yield a
            a.close()

* Do not have any specific logic and just want to create class using its ``__init__``? then add a provider attribute using ``provide`` as function passing that class.

.. code-block:: python

    class MyProvider(Provider):
        a = provide(A, scope=Scope.REQUEST)

* Want to create a child class instance when parent is requested? add a ``source`` attribute to ``provide`` function with a parent class while passing child as a first parameter

.. code-block:: python

    class MyProvider(Provider):
        a = provide(source=AChild, scope=Scope.REQUEST, provides=A)


* Want to go ``async``? Make provide methods asynchronous. Create async container. Use ``async with`` and await ``get`` calls:

.. code-block:: python

    class MyProvider(Provider):
       @provide(scope=Scope.APP)
       async def get_a(self) -> A:
          return A()

    async with make_async_container(MyProvider()) as container:
         a = await container.get(A)

* Tired of providing `scope==` for each depedency? Set it inside your `Provider` class and all factories with no scope will use it.

.. code-block:: python

    class MyProvider(Provider):
       scope=Scope.APP

       @provide  # uses provider scope
       async def get_a(self) -> A:
          return A()

       @provide(scope=Scope.REQUEST)  # has own scope
       async def get_b(self) -> B:
          return B()
