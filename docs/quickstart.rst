Quickstart
********************

1. Install dishka

.. code-block:: shell

    pip install dishka


2. Create Provider instance. It is only used co setup all factories providing your objects.

.. code-block:: python

    from dishka import Provider

    provider = Provider()

3. Register functions which provide dependencies. Do not forget to place correct typehints for parameters and result. We use ``scope=Scope.APP`` for dependencies which ar created only once in applicaiton lifetime, and ``scope=Scope.REQUEST`` for those which should be recreated for each processing request/event/etc.

.. code-block:: python

   from dishka import Provider, Scope

   def get_a() -> A:
       return A()

   def get_b(a: A) -> B:
       return B(a)

   provider = Provider()
   provider.provide(get_a, scope=Scope.APP)
   provider.provide(get_b, scope=Scope.REQUEST)

This can be also rewritten using class:

.. code-block:: python

   from dishka import provide, Provider, Scope

   class MyProvider(Provider):
      @provide(scope=Scope.APP)
      def get_a(self) -> A:
         return A()

      @provide(scope=Scope.REQUEST)
      def get_b(self, a: A) -> B:
         return B(a)

   provider = MyProvider()

4. Create Container instance passing providers, and step into ``APP`` scope. Container holds dependencies cache and is used to retrieve them. Here, you can use ``.get`` method to access APP-scoped dependencies:

.. code-block:: python

   from dishka import make_container

   container = make_container(provider)  # it has Scope.APP
   a = container.get(A)  # `A` has Scope.APP, so it is accessible here


5. You can enter and exit ``REQUEST`` scope multiple times after that using context manager:

.. code-block:: python

   from dishka import make_container

   container = make_container(MyProvider())
   with container() as request_container:
       b = request_container.get(B)  # `B` has Scope.REQUEST
       a = request_container.get(A)  # `A` is accessible here too

   with container() as request_container:
       b = request_container.get(B)  # another instance of `B`
       a = request_container.get(A)  # the same instance of `A`

6. Close container in the end:

.. code-block:: python

   container.close()


6. If you are using supported framework add decorators and middleware for it.


.. code-block:: python

    from dishka.integrations.fastapi import (
        Depends, inject, DishkaApp,
    )

    @router.get("/")
    @inject
    async def index(a: Annotated[A, Depends()]) -> str:
        ...

    ...
    app = DishkaApp(
        providers=[MyProvider()],
        app=app,
    )