.. _ru-aiogram_dialog:

aiogram-dialog
===========================================

Хотя это и не обязательно, вы можете использовать интеграцию ``dishka-aiogram_dialog``. Она позволяет внедрять зависимости в обработчики ``aiogram-dialog``.

Как использовать
****************

1. Настройка интеграции :ref:`aiogram integration<ru-aiogram>`

2. Импорт декоратора

.. code-block:: python

    from dishka.integrations.aiogram_dialog import inject

3. Пометьте параметры ваших обработчиков и геттеров ``aiogram-dialog``, которые должны внедряться через ``FromDishka[]``, используя импортированный декоратор ``@inject``

..  code-block:: python

    @inject
    async def getter(
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
        **kwargs,
    ):
        ...


    @inject
    async def on_click(
        event,
        widget,
        manager,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ):
        ...
