.. _ru-celery:

Celery
============================

Хотя это не обязательно, вы можете использовать интеграцию ``dishka-celery``. Она предоставляет следующие возможности:

* Автоматическое управление областью видимости *REQUEST* с помощью сигналов
* Внедрение зависимостей в функцию-обработчик задачи с помощью декоратора
* Автоматическое внедрение зависимостей в функцию-обработчик задачи

Как использзовать
********************

1. Импорт

.. code-block:: python

    from dishka.integrations.celery import (
        DishkaTask,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope


2. Создание провайдера и контейнера (как обычно)

3. *(опционально)* Установите класс задачи (task class) для вашего Celery-приложения, чтобы включить автоматическое внедрение для всех обработчиков задач

.. code-block:: python

    celery_app = Celery(task_cls=DishkaTask)

или для одного обработчика

.. code-block:: python

    @celery_app.task(base=DishkaTask)
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

4. Пометьте параметры функции-обработчика, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @celery_app.task
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

5. *(опционально)* Декорируйте их с помощью ``@inject``, если не используете ``DishkaTask``

.. code-block:: python

    @celery_app.task
    @inject
    def start( 
        gateway: FromDishka[Gateway],
    ):
        ...

6. *(опционально)* Настройте сигнал для закрытия контейнера при завершении работы воркера

.. code-block:: python

    from celery import current_app
    from celery.signals import worker_process_shutdown
    from dishka import Container

    @worker_process_shutdown.connect()
    def close_dishka(*args, **kwargs):
        container: Container = current_app.conf["dishka_container"]
        container.close()

7. Настройте интеграцию ``dishka``

.. code-block:: python

    setup_dishka(container=container, app=celery_app)
