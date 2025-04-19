.. _ru-arq:

arq
================

Хотя это и не обязательно, вы можете использовать интеграцию dishka-taskiq. Она предоставляет следующие возможности:

* Автоматическое управление областью видимости *REQUEST* с помощью middleware
* Внедрение зависимостей в функцию-обработчик задач с помощью декоратора

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.arq import (
        FromDishka,
        inject,
        setup_dishka,
    )

2. Создайте провайдер и контейнер как обычно

3. Пометьте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]`` и примените к ним декоратор ``@inject``

.. code-block:: python

    @inject
    async def get_content(
        context: dict[Any, Any],
        gateway: FromDishka[Gateway],
    ):
        ...

4. Настройте интеграцию ``dishka`` в вашем классе ``Worker`` или напрямую в ``WorkerSettings``

.. code-block:: python

    setup_dishka(container=container, worker_settings=WorkerSettings)
