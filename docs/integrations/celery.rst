.. _celery:

Celery
============================


Though it is not required, you can use dishka-celery integration. It features:

* automatic REQUEST scope management using signals
* injection of dependencies into task handler function using decorator
* automatic injection of dependencies into task handler function


How to use
****************

1. Import

.. code-block:: python

    from dishka.integrations.celery import (
        DishkaTask,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope


2.  Create provider and container as usual
3. (optional) Set task class to your celery app to enable automatic injection for all task handlers

.. code-block:: python

    celery_app = Celery(task_cls=DishkaTask)

or for one task handler

.. code-block:: python

    @celery_app.task(base=DishkaTask)
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

4. Mark those of your task handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @celery_app.task
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

5. (optional) Decorate them using ``@inject`` if you are not using ``DishkaTask``.

.. code-block:: python

    @celery_app.task
    @inject
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

6. (optional) Setup signal to close container when worker process shutdown 

.. code-block:: python

    from celery import current_app
    from celery.signals import worker_process_shutdown
    from dishka import Container

    @worker_process_shutdown.connect()
    def close_dishka(*args, **kwargs):
        container: Container = current_app.conf["dishka_container"]
        container.close()

7. Setup dishka integration

.. code-block:: python

    setup_dishka(container=container, app=celery_app)
