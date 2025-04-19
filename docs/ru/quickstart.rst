Quickstart
********************

1. **Установка Dishka.**

.. code-block:: shell

    pip install dishka

2. **Определите пользовательские классы с использованием type hints.** Представьте, что у вас есть два класса: ``Service`` (бизнес логика) и
   ``DAO`` (доступ к данным),  а также клиент внешнего API:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 6-21

3. **Создайте** экземпляр класса ``Provider`` и укажите как предоставлять зависимости.

Провайдеры используются только для настройки Фабрик, которые создают ваши объекты.

Используйте ``scope=Scope.APP`` для зависимостей, которые создаются один раз на всё время работы приложения,
и ``scope=Scope.REQUEST`` для тех, которые должны пересоздаваться при каждом запросе, событии и т. д.

Подробнее об областях видимости (scopes) см. в разделе :ref:`scopes`.

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 24-30

Чтобы предоставить освобождаемое (управляемое) соединение, может потребоваться специальный код:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 33-41

4. **Создайте основной экзепляр** ``Container``, передав ему провайдеры, и войдите в область видимости ``APP``.

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 44-47

5. **Получайте зависимости через контейнер.** Контейнер хранит кэш зависимостей и используется для их извлечения.
Вы можете использовать метод ``.get`` для доступа к зависимостям с областью видимости ``APP``:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 49-50

6. **Входите и выходите** из области видимости ``REQUEST`` многократно, используя контекстный менеджер:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 52-60

7. **Закройте контейнер** когда завершите работу с ним:

.. literalinclude:: ./quickstart_example.py
   :language: python
   :lines: 62

8. **Интеграция с вашим фреймворком.**  Если вы используете один из поддерживаемых фреймворков, то добавьте декораторы и middleware для него.
   Подробнее см. в разделе :ref:`integrations`

.. code-block:: python

    from dishka.integrations.fastapi import (
        FromDishka, inject, setup_dishka,
    )


    @router.get("/")
    @inject
    async def index(service: FromDishka[Service]) -> str:
        ...


    ...
    setup_dishka(container, app)
