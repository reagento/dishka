.. _ru-click:

Click
=================================

Хотя это не является обязательным, вы можете использовать интеграцию ``dishka-click``. Она предоставляет автоматическую инъекцию зависимостей в обработчики команд.
В отличие от других интеграций, здесь отсутствует управление областями видимости (scope management).

Как использовать
********************

1. Импорт

.. code-block:: python

    from dishka.integrations.click import setup_dishka, inject

2. Создайте контейнер в групповом обработчике и настройте его для контекста click. Передайте ``auto_inject=True``, если вы не хотите явно использовать декоратор ``@inject``.

.. code-block:: python

    @click.group()
    @click.pass_context
    def main(context: click.Context):
        container = make_container(MyProvider())
        setup_dishka(container=container, context=context, auto_inject=True)

3. Пометьте те параметры ваших обработчиков команд, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @main.command(name="hello")
    def hello(interactor: FromDishka[Interactor]):
        ...

3a. *(опционально)* Декорируйте их с использованием ``@inject``.

.. code-block:: python

    @main.command(name="hello")
    @inject
    def hello(interactor: FromDishka[Interactor]):
        ...