.. _ru-taskiq:

taskiq
===========================================

Хотя это не является обязательным, вы можете использовать интеграцию ``dishka-taskiq`` . Она включает следующие возможности:

* автоматическое управление областью видимости *REQUEST* с помощью middleware;
* передачу объекта ``TaskiqMessage`` как контекстных данных в провайдеры;
* внедрение зависимостей в обработчики задач с помощью декоратора.


Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.taskiq import (
        FromDishka,
        inject,
        setup_dishka,
        TaskiqProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создание провайдера. Вы можете использовать ``taskiq.TaskiqMessage`` в качестве параметра фабрики для доступа к *REQUEST*-области (контексту запроса).

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TaskiqMessage) -> X:
             ...

3. Помечайте параметры обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``, и декорируйте их с помощью ``@inject``.

.. code-block:: python

    @broker.task
    @inject(patch_module=True)
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...

.. warning::
    В версии 1.5 был добавлен параметр ``patch_module`` в декоратор ``@inject``, который отвечает за переопределение атрибута ``__module__`` у функции, участвующей в формировании ``task_name``.

    Рекомендуется использовать значение ``patch_module=True`` для корректной генерации ``task_name`` по умолчанию в соответствии с модулем, в котором был определён обработчик задачи.

    Значение по умолчанию — ``False``, для обратной совместимости с версиями < 1.5. В будущих релизах значение по умолчанию может быть изменено на ``True``.

4. *(опционально)* Используйте ``TaskiqProvider()`` при создании контейнера, если вы планируете использовать ``taskiq.TaskiqMessage`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), TaskiqProvider())

5. Настройка интеграции ``dishka``.

.. code-block:: python

    setup_dishka(container=container, broker=broker)

