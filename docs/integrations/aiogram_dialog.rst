.. _aiogram_dialog:

aiogram-dialog
===========================================


Though it is not required, you can use *dishka-aiogram_dialog* integration. It allows you to inject object into ``aiogram-dialog`` handlers.


How to use
****************

1. Setup :ref:`aiogram integration<aiogram>`

2. Import decorator

.. code-block:: python

    from dishka import FromDishka
    from dishka.integrations.aiogram_dialog import inject


3. Mark those of your ``aiogram-dialog`` handlers and getters parameters which are to be injected with ``FromDishka[]`` decorate them using imported ``@inject`` decorator.

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
