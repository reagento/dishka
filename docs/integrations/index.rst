Using with frameworks
*******************************

There are some integrations in library you are not limited to use them.

Built-in frameworks integrations:

* aiohttp
* Flask
* Fastapi
* Litestar
* Starlette
* Aiogram
* pyTelegramBotAPI
* Arq
* FastStream
* TaskIq

Common approach
=====================

For several frameworks library contains helper functions so you don't need to control scopes yourself, but just annotate handler/view functions and change application startup code

To use framework integration you mainly need to do 3 things:

* call ``setup_dishka`` on your container and framework entity
* add ``Annotated[YourClass, FromDishka()]`` on you framework handlers (or view-functions)
* decorate your handlers with ``@inject`` before registering them in framework. Some integrations do not required it, see :ref:`autoinject`

For FastAPI it will look like:

.. code-block:: python

   from dishka.integrations.fastapi import FromDishka, inject, setup_dishka

   @router.get("/")
   @inject
   async def index(interactor: Annotated[Interactor, FromDishka()]) -> str:
       result = interactor()
       return result

   app = FastAPI()
   container = make_async_container(provider)
   setup_dishka(container, app)


For such integrations library enters scope for each generated event. So if you have standard scope, than handler dependencies will be retrieved as for ``Scope.REQUEST``.

Additionally, you may need to call ``container.close()`` in the end of your application lifecycle if you want to finalize APP-scoped dependencies

.. _autoinject:

Auto injection
=========================

With some frameworks we provide an option to inject dependencies in handlers without decorating them with ``@inject``.

* For **aiogram** you need to provide ``auto_inject=True`` when calling ``setup_dishka``. E.g:

.. code-block:: python

    from dishka.integrations.aiogram import FromDishka, setup_dishka

    @router.message()
    async def start(
        message: Message,
        user: Annotated[User, FromDishka()],
    ):
        await message.answer(f"Hello, {1}, {user.full_name}!")


    setup_dishka(container=container, router=dp, auto_inject=True)

* For **Flask** you need to provide ``auto_inject=True`` when calling ``setup_dishka``. It is important here to call it after registering all views and blueprints. E.g:

.. code-block:: python

    from dishka.integrations.flask import FromDishka, setup_dishka

    @app.get("/"
    def index(
            *,
            interactor: Annotated[Interactor, FromDishka()],
    ) -> str:
        result = interactor()
        return result

    setup_dishka(container=container, app=app, auto_inject=True)

* For **FastAPI** you need to provide ``route_class=DishkaRoute`` when creating ``APIRouter``. E.g.:

.. code-block:: python

    from dishka.integrations.fastapi import FromDishka, setup_dishka

    router = APIRouter(route_class=DishkaRoute)

    @router.get("/")
    async def index(
            *,
            interactor: Annotated[Interactor, FromDishka()],
    ) -> str:
        result = interactor()
        return result

    setup_dishka(container, app)


Adding integrations
===========================

Though there are some integrations in library you are not limited to use them.

The main points are:

1. Find a way to pass a global container instance. Often it is attached to application instance or passed by a middleware.
2. Find a place to enter request scope and how to pass it to a handler. Usually, it is entered in a middleware and container is stored in some kind of request context.
3. Configure a decorator. The main option here is to provide a way for retrieving container. Often, need to modify handler signature adding additional parameters. It is also available.
4. Check if you can apply decorator automatically.

While writing middlewares and working with scopes is done by your custom code, we have a helper for creating ``@inject`` decorators - a ``wrap_injection`` function.

* ``container_getter`` is a function with two params ``(args, kwargs)`` which is called to get a container used to retrieve dependencies within scope.
* ``additional_params`` is a list of ``inspect.Parameter`` which should be added to handler signature.

For more details, check existing integrations.
