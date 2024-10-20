.. _taskiq:

taskiq
===========================================

Though it is not required, you can use dishka-taskiq integration. It features:

* automatic REQUEST scope management using middleware
* passing ``TaskiqMessage`` object as a context data to providers
* injection of dependencies into task handler function using decorator


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.taskiq import (
        FromDishka,
        inject,
        setup_dishka,
        TaskiqProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``taskiq.TaskiqMessage`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TaskiqMessage) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @broker.task
    @inject
    async def start(
        gateway: FromDishka[Gateway],
    ):


4. *(optional)* Use ``TaskiqProvider()`` when creating container if you are going to use ``taskiq.TaskiqMessage`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), TaskiqProvider())


6. Setup dishka integration.

.. code-block:: python

    setup_dishka(container=container, broker=broker)

