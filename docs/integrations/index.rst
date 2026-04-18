.. include:: <isonum.txt>

.. _integrations:

Using with frameworks
*******************************

There are some integrations in library, however you are not limited to them only.
You can create custom integrations for your framework of choice.
Some of the integrations are supported by a community, refer to their documentation as well.

.. toctree::
   :hidden:

   ag2 <https://github.com/C3EQUALZz/dishka-ag2>
   aiogram
   aiogram_dialog
   aiohttp
   arq
   celery
   click
   fastapi
   faststream
   flask
   flet <https://github.com/C3EQUALZz/dishka-flet>
   grpcio
   jobify <https://github.com/Jobify-Community/dishka-jobify>
   litestar
   Pyramid <https://github.com/WorkHardes/dishka-pyramid>
   RQ <https://github.com/prepin/dishka-rq>
   sanic
   starlette
   Strawberry <https://github.com/aryadovoy/dishka-strawberry>
   taskiq
   telebot
   Quart <https://github.com/hrimov/quart-dishka>
   apscheduler <https://github.com/MikhailWar/apscheduler-dishka>
   adding_new

.. list-table:: Built-in frameworks integrations
   :header-rows: 1

   * - Web frameworks
     - Telegram bots
     - Tasks and events
     - Other

   * -  :ref:`aiohttp`
     -  :ref:`aiogram`
     -  :ref:`arq`
     -  :ref:`Click`

   * - :ref:`grpcio`
     - :ref:`Aiogram_dialog`
     - `FastStream  <https://github.com/faststream-community/dishka-faststream>`_ (:abbr:`com (Community support)`)
     - `Flet <https://github.com/C3EQUALZz/dishka-flet>`_ (:abbr:`com (Community support)`)

   * - :ref:`Fastapi`
     - :ref:`pyTelegramBotAPI<telebot>`
     - :ref:`TaskIq`
     - `ag2 <https://github.com/C3EQUALZz/dishka-ag2>`_ (:abbr:`com (Community support)`)

   * - :ref:`Flask`
     -
     - :ref:`Celery`
     -
   * -  :ref:`Litestar`
     -
     - `RQ <https://github.com/prepin/dishka-rq>`_ (:abbr:`com (Community support)`)
     -
   * - `Pyramid <https://github.com/WorkHardes/dishka-pyramid>`_ (:abbr:`com (Community support)`)
     -
     - `Jobify <https://github.com/Jobify-Community/dishka-jobify>`_ (:abbr:`com (Community support)`)
     -
   * -  :ref:`Sanic`
     -
     - `APScheduler <https://github.com/MikhailWar/apscheduler-dishka>`_ (:abbr:`com (Community support)`)
     -
   * -  `Starlette <https://github.com/reagento/starlette-dishka>`_ (:abbr:`com (Community support)`)
     -
     -
     -
   * - `Strawberry <https://github.com/aryadovoy/dishka-strawberry>`_ (:abbr:`com (Community support)`)
     -
     -
     -
   * -  `Quart <https://github.com/hrimov/quart-dishka>`_ (:abbr:`com (Community support)`)
     -
     -
     -

If you have another framework  refer :ref:`adding_new`


See also the real `integration examples <https://github.com/reagento/dishka/tree/develop/examples/integrations>`_ here.


Common approach
=====================

For several frameworks library contains helper functions so you don't need to control scopes yourself, but just annotate handler/view functions and change application startup code.

To use framework integration you mainly need to do 4 things:

* call ``setup_dishka`` on your container and framework entity
* add ``FromDishka[YourClass]`` on you framework handlers (or view-functions)
* decorate your handlers with ``@inject`` before registering them in framework. Some integrations do not require it, see their details
* add additional provider to the container to access framework specific objects from your provider.

.. note::
   ``FromDishka[T]`` is basically a synonym for ``Annotated[T, FromComponent()]`` and is used to get an object from default component. To use other component you can use the same syntax with annotated ``Annotated[T, FromComponent("X")]``.

   For more details on components see :ref:`components`

For such integrations library enters scope for each generated event. So, if you have standard scope, than handler dependencies will be retrieved as for ``Scope.REQUEST``.
For streaming protocols and websockets you will be also to have *SESSION*-scoped objects with a lifespan of the whole stream.

Additionally, you may need to call ``container.close()`` in the end of your application lifecycle if you want to finalize *APP*-scoped dependencies.

Some frameworks have their own specific, check corresponding page.

For ``FastAPI`` it will look like:

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
