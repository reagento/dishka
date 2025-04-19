.. _arq:

arq
================

Though it is not required, you can use dishka-taskiq integration. It features:

* automatic *REQUEST* scope management using middleware
* injection of dependencies into task handler function using decorator


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.arq import (
        FromDishka,
        inject,
        setup_dishka,
    )

2. Create provider and container as usual

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @inject
    async def get_content(
        context: dict[Any, Any],
        gateway: FromDishka[Gateway],
    ):
        ...

4. Setup ``dishka`` integration on your ``Worker`` class or directly on ``WorkerSettings``

.. code-block:: python

    setup_dishka(container=container, worker_settings=WorkerSettings)
