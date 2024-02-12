Quickstart
********************

1. Install dishka

.. code-block:: shell

    pip install dishka


2. Create Provider subclass.

.. code-block:: python

    from dishka import Provider
    class MyProvider(Provider):
       ...

3. Mark methods which actually create dependencies with `@provide` decorator with carefully arranged scopes. Do not forget to place correct typehints for parameters and result.
Here we describe how to create instances of A and B classes, where B class requires itself an instance of A.

.. code-block:: python

    from dishka import provide, Provider, Scope
    class MyProvider(Provider):
       @provide(scope=Scope.APP)
       def get_a(self) -> A:
          return A()

       @provide(scope=Scope.REQUEST)
       def get_b(self, a: A) -> B:
          return B(a)

4. Create Container instance passing providers, and step into `APP` scope. Or deeper if you need.

.. code-block:: python

    from dishka import make_container
    with make_container(MyProvider()) as container:  # enter Scope.APP
         with container() as request_container:   # enter Scope.REQUEST
              ...


5. Call `get` to get dependency and use context manager to get deeper through scopes

.. code-block:: python

    from dishka import make_container
    with make_container(MyProvider()) as container:
         a = container.get(A)  # `A` has Scope.APP, so it is accessible here
         with container() as request_container:
              b = request_container.get(B)  # `B` has Scope.REQUEST
              a = request_container.get(A)  # `A` is accessible here too


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