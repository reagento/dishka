Using with frameworks
*******************************

For several frameworks library contains helper functions so you don't need to control scopes yourself, but just annotate handler/view functions and change application startup code

To use framework integration you mainly need to do 3 things:

* call ``setup_dishka`` on your container and framework entity
* add ``Annotated[YourClass, FromDishka()]`` on you framework handlers (or view-functions)
* decorate your handlers with ``@inject`` before registering them in framework

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