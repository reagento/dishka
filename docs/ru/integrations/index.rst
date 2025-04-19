.. include:: <isonum.txt>

.. _ru-integrations:

Использование с фреймворками
*******************************

В библиотеке есть несколько готовых интеграций, однако вы не ограничены только ими.
Вы можете создать собственные интеграции для выбранного вами фреймворка.
Некоторые интеграции поддерживаются сообществом — обратитесь к их документации для получения дополнительной информации.

.. toctree::
   :hidden:

   aiogram
   aiogram_dialog
   aiohttp
   arq
   celery
   click
   fastapi
   faststream
   flask
   grpcio
   litestar
   RQ <https://github.com/prepin/dishka-rq>
   sanic
   starlette
   taskiq
   telebot
   Quart <https://github.com/hrimov/quart-dishka>
   adding_new

.. list-table:: Встроенные интеграции с фреймворками
   :header-rows: 1

   * - Web-фреймворки
     - Telegram-боты
     - Таски и события
     - Другое

   * -  :ref:`aiohttp`
     -  :ref:`aiogram`
     -  :ref:`arq`
     -  :ref:`Click`

   * - :ref:`grpcio`
     - :ref:`Aiogram_dialog`
     - :ref:`FastStream`
     -

   * - :ref:`Fastapi`
     - :ref:`pyTelegramBotAPI<telebot>`
     - :ref:`TaskIq`
     -

   * - :ref:`Flask`
     -
     - :ref:`Celery`
     -
   * -  :ref:`Litestar`
     -
     - `RQ <https://github.com/prepin/dishka-rq>`_ (:abbr:`com (Community support)`)
     -
   * -  :ref:`Sanic`
     -
     -
     -
   * -  :ref:`Starlette`
     -
     -
     -
   * -  `Quart <https://github.com/hrimov/quart-dishka>`_ (:abbr:`com (Community support)`)
     -
     -
     -

если вы используете другой фреймворк, см. раздел :ref:`adding_new`


Также посмотрите реальные примеры интеграций `integration examples <https://github.com/reagento/dishka/tree/develop/examples/integrations>`_ здесь.


Общий подход
=====================

Для многих фреймворков библиотека предоставляет вспомогательные функции, так что вам не нужно управлять областями видимости (scopes) вручную. Вместо этого достаточно аннотировать обработчики или view-функции и изменить код запуска приложения.

Чтобы использовать интеграцию с фреймворком, обычно нужно выполнить 4 шага:

* Вызвать ``setup_dishka`` для вашего контейнера и сущности фреймворка
* Добавить ``FromDishka[YourClass]`` к обработчикам фреймворка (или view-функциям)
* Декорировать обработчики с помощью ``@inject`` перед их регистрацией во фреймворке. Некоторые интеграции не требуют этого — см. их описание
* Добавить дополнительный провайдер в контейнер, чтобы получить доступ к специфичным для фреймворка объектам из вашего провайдера

.. note::
    ``FromDishka[T]`` по сути является синонимом для ``Annotated[T, FromComponent()]`` и используется для получения объекта из компонента по умолчанию. Чтобы использовать другой компонент, можно применить аналогичный синтаксис с аннотацией ``Annotated[T, FromComponent("X")]``.

    Подробнее о компонентах см. :ref:`components`


При такой интеграции библиотека создаёт область видимости для каждого сгенерированного события. Таким образом, если у вас стандартная область видимости, зависимости обработчика будут извлекаться как для ``Scope.REQUEST``.
Для потоковых протоколов и вебсокетов также будут доступны объекты с областью видимости ``SESSION``, существующие на протяжении всего потока данных.

Кроме того, может потребоваться вызвать ``container.close()`` в конце жизненного цикла приложения, если нужно завершить зависимости с областью видимости APP.

Некоторые фреймворки имеют свои особенности — см. соответствующую документацию.

Для FastAPI это будет выглядеть так:

.. code-block:: python

   from dishka.integrations.fastapi import FromDishka, inject, setup_dishka, FastapiProvider

   @router.get("/")
   @inject
   async def index(interactor: FromDishka[Interactor]) -> str:
       result = interactor()
       return result

   app = FastAPI()
   container = make_async_container(your_provider, FastapiProvider())
   setup_dishka(container, app)

